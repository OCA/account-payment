import logging
import re
from base64 import b64encode

from iso8601 import parse_date
import requests
import phonenumbers as pn
import coreapi
from hal_codec import HALCodec


SLIMPAY_FORBIDEN_CHARS_RE = re.compile(r'[0-9@/\\]')

_logger = logging.getLogger(__name__)


def get_token(api_url, app_id, app_secret):
    auth = b64encode(b':'.join((bytes(app_id, 'utf-8'), bytes(app_secret, 'utf-8'))))
    resp = requests.post(
        '%s/oauth/token' % api_url,
        headers={'Accept': 'application/json',
                 'Authorization': 'Basic %s' % auth.decode('utf-8'),
                 'Content-Type': 'application/x-www-form-urlencoded'},
        data={'grant_type': 'client_credentials', 'scope': 'api'})
    resp.raise_for_status()
    return resp.json()['access_token']


def get_client(api_url, app_id, app_secret, **kwargs):
    token = get_token(api_url, app_id, app_secret)
    _logger.debug('Got token %s', token)
    transport = coreapi.transports.HTTPTransport(
        headers={'Authorization': 'Bearer %s' % token})
    codec = HALCodec()
    return coreapi.Client(decoders=[codec], transports=[transport])


def _signed_date(mandate):
    return parse_date(mandate['dateSigned'])


def partner_mobile_phone(partner, fields=('phone', 'mobile')):
    """If possible, supply a valid mobile phone number to Slimpay, to
    simplify end-user's life. If found, return it E164 formatted.

    The method searches the given `partner`'s `fields` for a
    mobile phone, and uses its country to parse it. If no country
    was found, use France as a default (slimpay is mostly a
    french company for the moment).
    """
    region = partner.country_id.code if partner.country_id.code else 'FR'

    for field in fields:
        phone = getattr(partner, field)
        if phone:
            try:
                parsed = pn.parse(phone, region=region)
            except pn.NumberParseException:
                continue
            if pn.number_type(parsed) == pn.PhoneNumberType.MOBILE:
                return pn.format_number(parsed, pn.PhoneNumberFormat.E164)


def slimpay_normalize_names(name):
    """As of november 2019, the doc states (for givenName and familyName):
      Are forbidden:

      digits from 0 to 9
      the at sign @
      the slash /
      the backslash \

    (see https://dev.slimpay.com/hapi/guide/checkout/setting-up-direct-debits)
    """
    return SLIMPAY_FORBIDEN_CHARS_RE.sub('', name or '')


def subscriber_from_partner(partner):
    data = {
        "familyName": slimpay_normalize_names(partner.lastname) or None,
        "givenName": slimpay_normalize_names(partner.firstname) or None,
        "telephone": partner_mobile_phone(partner),
        "email": partner.email or None,
        "billingAddress": {
            "street1": partner.street or None,
            "street2": partner.street2 or None,
            "postalCode": partner.zip or None,
            "city": partner.city or None,
            "country": partner.country_id.code or None,
        }
    }
    return {'reference': partner.id, 'signatory': data}


class SlimpayClient(object):

    def __init__(self, api_url, creditor, app_id, app_secret):
        self.api_url = api_url
        self.creditor = creditor
        self.app_id = app_id
        self.app_secret = app_secret
        self._client = get_client(api_url, app_id, app_secret)
        self._root_doc = None

    def action(self, action, short_method_name, validate=False, params=None,
               doc=None):
        if doc is None:
            doc = self.root_doc
        return self._client.action(
            doc, self.method_name(short_method_name),
            action=action, validate=validate, params=params)

    def approval_url(self, tx_ref, order_id, locale, amount, currency,
                     decimal_places, subscriber, notify_url):
        """ Return the URL a final user must visit to perform a mandate
        signature with a first payment.

        `order_id` is the internal order db identifier (an int, e.g. 402)
        `locale` is the language locale of the user (e.g.: "fr")
        `amount` and `currency` designate the initial payment value
        `subscriber` designate a dict with keys 'reference' and 'signatory' as
        obtained using with `subscriber_from_partner`.
        `notify_url` is the URL to be notified at the end of the operation.
        """
        params = self._repr_order(
            tx_ref, order_id, locale, amount, currency, decimal_places,
            subscriber, notify_url)
        _logger.debug("slimpay approval_url parameters: %s", params)
        order = self.action('POST', 'create-orders', params=params)
        url = order.links[self.method_name('user-approval')].url
        _logger.debug("User approval URL is: %s", url)
        return url

    def create_payment(self, mandate_ref, amount, currency, label, out=False):
        """ Create a Slimpay payin or payout depending on `out` boolean value.
        Returns False if it fails, otherwise Slimpay payment's reference.
        """
        if out:
            scheme = 'SEPA.CREDIT_TRANSFER'
            method = 'create-payouts'
        else:
            scheme = 'SEPA.DIRECT_DEBIT.CORE'
            method = 'create-payins'
        params = {
            'creditor': {'reference': self.creditor},
            'mandate': {'reference': mandate_ref},
            'label': label,
            'amount': amount,
            'currency': currency,
            'scheme': scheme,
            'executionDate': None,  # means ASAP
        }
        _logger.debug('Payment creation with params: %s (method: %s)',
                      params, method)
        response = self.action('POST', method, params=params)
        _logger.debug('%s reponse: %s', method, response)
        if response.get('executionStatus') != 'toprocess':
            _logger.error(
                'Invalid slimpay payment response for transaction:\n %r',
                response)
            return False
        return response.get('state') == 'accepted' and response['reference']

    def get(self, url):
        """ Expose the raw coreapi `get` method """
        return self._client.get(url)

    def get_from_doc(self, doc, short_method_name):
        """ Fetch the `short_method_name` method from given document `doc` """
        return self._client.get(doc[self.method_name(short_method_name)].url)

    def last_valid_mandate(self, subscriber_ref):
        """Return the most recently signed active mandate which matches given
        search criterias
        (see https://dev.slimpay.com/hapi/reference/mandates#search-mandates)
        """
        search_params = {'creditorReference': self.creditor,
                         'subscriberReference': subscriber_ref}
        doc = self.action('GET', 'search-mandates', params=search_params)
        if 'mandates' in doc:
            ordered_valid = [
                m for m in sorted(doc['mandates'], key=_signed_date)
                if m['state'] == 'active']
            if ordered_valid:
                return ordered_valid[-1]

    def method_name(self, name):
        """ Return complete slimpay API method from its given short name """
        return 'https://api.slimpay.net/alps#%s' % name

    @property
    def root_doc(self):
        if self._root_doc is None:
            self._root_doc = self._client.get(self.api_url)
        return self._root_doc

    def _repr_mandate(self, subscriber):
        return {
            'type': 'signMandate',
            'mandate': {
                'action': 'sign',
                'paymentScheme': 'SEPA.DIRECT_DEBIT.CORE',
                'signatory': subscriber['signatory'],
            },
        }

    def _repr_order(self, tx_ref, order_id, locale, amount, currency,
                    decimal_places, subscriber, notify_url):
        return {
            'reference': tx_ref,
            'locale': locale,
            'creditor': {'reference': self.creditor},
            'subscriber': {'reference': subscriber['reference']},
            'started': True,
            'items': [
                self._repr_mandate(subscriber),
                self._repr_payment(order_id, amount, currency, decimal_places,
                                   notify_url),
            ],
        }

    def _repr_payment(self, label, amount, currency, decimal_places,
                      notify_url):
        return {
            'type': 'payment',
            'action': 'create',
            'payin': {
                'scheme': 'SEPA.DIRECT_DEBIT.CORE',
                'direction': 'IN',
                'amount': round(amount, decimal_places),
                'currency': currency,
                'label': label,
                'notifyUrl': notify_url,
            }
        }
