import logging
from base64 import b64encode

import requests
import phonenumbers
import coreapi
from hal_codec import HALCodec
from iso8601 import parse_date

from odoo import models, fields


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
        size=32,
        required_if_provider='slimpay',
        groups='base.group_user')
    slimpay_app_id = fields.Char(
        'OAuth application Id',
        size=32,
        required_if_provider='slimpay',
        groups='base.group_user')
    slimpay_app_secret = fields.Char(
        'OAuth application Secret',
        size=32,
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

    def slimpay_mobile_phone(self, partner):
        "Slimpay requires a mobile phone. Find one for partner or return None"
        for phone in (partner.phone, partner.mobile):
            if phone:
                try:
                    parsed = phonenumbers.parse(
                        phone, partner.country_id.code.upper())
                except phonenumbers.NumberParseException:
                    continue
                if (phonenumbers.number_type(parsed)
                        == phonenumbers.PhoneNumberType.MOBILE):
                    return phone

    def slimpay_signatory(self, partner):
        data = {
            "familyName": partner.lastname,
            "givenName": partner.firstname,
            "email": partner.email,
            "billingAddress": {
                "street1": partner.street,
                "street2": partner.street2 or None,
                "telephone": self.slimpay_mobile_phone(partner),
                "postalCode": partner.zip,
                "city": partner.city,
                "country": partner.country_id.code,
            }
        }
        return data

    def slimpay_get_approval_url(self, so, partner, notify_url):
        root = self.slimpay_root_doc
        params = {
            'reference': so.name,
            'locale': self.env.context['lang'].split('_')[0],
            'creditor': {'reference': self.slimpay_creditor},
            'subscriber': {'reference': partner.id},
            'started': True,
            'items': [
                {
                    'type': 'signMandate',
                    'mandate': {
                        'action': 'sign',
                        'paymentScheme': 'SEPA.DIRECT_DEBIT.CORE',
                        'signatory': self.slimpay_signatory(partner),
                    },
                },
                {
                    'type': 'payment',
                    'action': 'create',
                    'payin': {
                        'scheme': 'SEPA.DIRECT_DEBIT.CORE',
                        'direction': 'IN',
                        'amount': so.amount_total,
                        'currency': so.currency_id.name,
                        'label': so.name,
                        'notifyUrl': notify_url,
                    },
                },
            ],
        }
        _logger.debug("slimpay parameters: %s", params)
        order = self.slimpay_client.action(
            root, 'https://api.slimpay.net/alps#create-orders',
            validate=False, action='POST', params=params)
        url = order.links['https://api.slimpay.net/alps#user-approval'].url
        _logger.info("User approval URL is: %s", url)
        return url
