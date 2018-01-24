import logging
from base64 import b64encode

import requests
import phonenumbers
import coreapi
from hal_codec import HALCodec
from iso8601 import parse_date

from odoo import models, fields
from odoo.tools.safe_eval import safe_eval


_logger = logging.getLogger(__name__)


def _oauth_token(api_url, app_id, app_secret):
    auth = b64encode(':'.join((app_id, app_secret)))
    resp = requests.post(
        '%s/oauth/token' % api_url,
        headers={'Accept': 'application/json',
                 'Authorization': 'Basic %s' % auth,
                 'Content-Type': 'application/x-www-form-urlencoded'},
        data={'grant_type': 'client_credentials', 'scope': 'api'})
    resp.raise_for_status()
    return resp.json()['access_token']


def _signed_date(mandate):
    return parse_date(mandate['dateSigned'])


class PaymentAcquirerSlimpay(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('slimpay', 'Slimpay')])
    slimpay_api_url = fields.Char(
        'API base url',
        required_if_provider='slimpay',
        groups='base.group_user')
    slimpay_creditor = fields.Char(
        'Creditor reference',
        size=64,
        required_if_provider='slimpay',
        groups='base.group_user')
    slimpay_app_id = fields.Char(
        'OAuth application Id',
        size=64,
        required_if_provider='slimpay',
        groups='base.group_user')
    slimpay_app_secret = fields.Char(
        'OAuth application Secret',
        size=64,
        required_if_provider='slimpay',
        groups='base.group_user')

    @property
    def slimpay_client(self):
        if not hasattr(self, '_slimpay_client'):
            token = _oauth_token(self.slimpay_api_url,
                                 self.slimpay_app_id,
                                 self.slimpay_app_secret)
            _logger.debug('Got token %s', token)
            transport = coreapi.transports.HTTPTransport(
                headers={'Authorization': 'Bearer %s' % token})
            self._slimpay_client = coreapi.Client(decoders=[HALCodec()],
                                                  transports=[transport])
        return self._slimpay_client

    @property
    def slimpay_root_doc(self):
        if not hasattr(self, '_slimpay_root_doc'):
            self._slimpay_root_doc = self.slimpay_client.get(
                self.slimpay_api_url)
        return self._slimpay_root_doc

    def slimpay_get_valid_mandate(self, partner, **search_params):
        """Return the most recently signed active mandate which matches given
        search criterias
        (see https://dev.slimpay.com/hapi/reference/mandates#search-mandates)
        """
        search_params['creditorReference'] = self.slimpay_creditor
        search_params['subscriberReference'] = partner.id
        doc = self.slimpay_client.action(
            self.slimpay_root_doc,
            'https://api.slimpay.net/alps#search-mandates',
            params=search_params, action='GET')
        if 'mandates' in doc:
            ordered_valid = [
                m for m in sorted(doc['mandates'], key=_signed_date)
                if m['state'] == 'active']
            if ordered_valid:
                return ordered_valid[-1]

    def slimpay_mobile_phone(self, partner, fields=('phone', 'mobile')):
        """If possible, supply a valid mobile phone number to Slimpay, to
        simplify end-user's life. If found, return it E164 formatted.

        The method searches the given `partner`'s `fields` for a
        mobile phone, and uses its country to parse it. If no country
        was found, use France as a default (slimpay is mostly a
        french company for the moment).
        """
        region = 'FR'  # slimpay mainly supports France
        if partner.country_id.code:
            region = partner.country_id.code.upper()
        for field in fields:
            phone = getattr(partner, field)
            if phone:
                try:
                    parsed = phonenumbers.parse(phone, region=region)
                except phonenumbers.NumberParseException:
                    continue
                if (phonenumbers.number_type(parsed)
                        == phonenumbers.PhoneNumberType.MOBILE):
                    return phonenumbers.format_number(
                        parsed, phonenumbers.PhoneNumberFormat.E164)

    def _slimpay_api_signatory(self, partner):
        data = {
            "familyName": partner.lastname or None,
            "givenName": partner.firstname or None,
            "email": partner.email or None,
            "billingAddress": {
                "street1": partner.street or None,
                "street2": partner.street2 or None,
                "telephone": self.slimpay_mobile_phone(partner),
                "postalCode": partner.zip or None,
                "city": partner.city or None,
                "country": partner.country_id.code or None,
            }
        }
        return data

    def _slimpay_api_mandate(self, partner, notify_url):
        return {
            'type': 'signMandate',
            'mandate': {
                'action': 'sign',
                'paymentScheme': 'SEPA.DIRECT_DEBIT.CORE',
                'signatory': self._slimpay_api_signatory(partner),
            },
        }

    def _slimpay_api_payment(self, ref, amount, currency, partner, notify_url):
        return {
            'type': 'payment',
            'action': 'create',
            'payin': {
                'scheme': 'SEPA.DIRECT_DEBIT.CORE',
                'direction': 'IN',
                'amount': amount,
                'currency': currency.name,
                'label': ref,
                'notifyUrl': notify_url,
            }
        }

    def _slimpay_api_create_order(self, ref, amount, currency, partner,
                                  notify_url):
        return {
            'reference': ref,
            'locale': self.env.context.get('lang', 'fr_FR').split('_')[0],
            'creditor': {'reference': self.slimpay_creditor},
            'subscriber': {'reference': partner.id},
            'started': True,
            'items': [
                self._slimpay_api_mandate(partner, notify_url),
                self._slimpay_api_payment(ref, amount, currency, partner,
                                          notify_url),
            ],
        }

    def slimpay_get_approval_url(self, ref, amount, currency, partner,
                                 notify_url):
        root = self.slimpay_root_doc
        params = self._slimpay_api_create_order(
            ref, amount, currency, partner, notify_url)
        _logger.debug("slimpay parameters: %s", params)
        order = self.slimpay_client.action(
            root, 'https://api.slimpay.net/alps#create-orders',
            validate=False, action='POST', params=params)
        url = order.links['https://api.slimpay.net/alps#user-approval'].url
        _logger.debug("User approval URL is: %s", url)
        return url

    def _slimpay_s2s_validate(self, sale_order, posted_data):
        """The posted data is validated using a http request to slimpay's
        server (to ensure posted data has not been forged), then the
        transaction status is updated.
        """
        sale_order.ensure_one()
        assert sale_order.payment_acquirer_id.provider == 'slimpay'
        so_url = posted_data['_links']['self']['href']
        doc = self.slimpay_client.get(so_url)
        _logger.warning(doc)
        assert doc['reference'] == sale_order.name
        slimpay_state = doc['state']
        tx = sale_order.payment_tx_id
        tx_attrs = {
            'acquirer_reference': doc['id'],
        }
        if slimpay_state == 'closed.completed':
            tx_attrs['state'] = 'done'
            tx_attrs['date_validate'] = parse_date(doc['dateClosed'])
            tx.write(tx_attrs)
            if tx.sudo().callback_eval:
                safe_eval(tx.sudo().callback_eval, {'self': self})
            return True
        elif slimpay_state.startswith("closed.aborted"):
            tx_attrs['state'] = 'cancel'
        tx.write(tx_attrs)
        return False
