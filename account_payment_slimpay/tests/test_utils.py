from mock import patch

from odoo.tests.common import TransactionCase, at_install, post_install

from odoo.addons.account_payment_slimpay.models import slimpay_utils


@at_install(False)
@post_install(True)
class SlimpayUtilsTC(TransactionCase):

    def setUp(self):
        super(SlimpayUtilsTC, self).setUp()
        france = self.env['res.country'].search([('code', '=', 'FR')])
        self.partner = self.env['res.partner'].create(
            {'firstname': 'F', 'lastname': 'C/@\\é9', 'country_id': france.id})

    def check_phone_value(self, expected):
        actual = slimpay_utils.partner_mobile_phone(self.partner)
        if expected is None:
            self.assertIsNone(actual)
        else:
            self.assertEqual(expected, actual)

    def test_slimpay_mobile_phone(self):
        self.partner.write({'phone': None})
        self.check_phone_value(None)
        self.partner.write({'phone': '06.01.02.03.04'})
        self.check_phone_value('+33601020304')

    def test_slimpay_signatory(self):
        subscriber = slimpay_utils.subscriber_from_partner(self.partner)
        self.assertEqual(
            {'familyName': 'Cé', 'email': None, 'givenName': 'F',
             'telephone': None, 'billingAddress': {
                 'city': None,
                 'country': 'FR',
                 'postalCode': None,
                 'street1': None,
                 'street2': None}
             }, subscriber['signatory'])
        self.assertEqual(self.partner.id, subscriber['reference'])

        self.partner.write({'street': '2 rue de Rome', 'street2': 'Appt X',
                            'zip': '67000', 'city': 'Strasbourg'})
        subscriber = slimpay_utils.subscriber_from_partner(self.partner)
        self.assertEqual(self.partner.id, subscriber['reference'])
        self.assertEqual(
            {'familyName': 'Cé', 'email': None, 'givenName': 'F',
             'telephone': None, 'billingAddress': {
                 'city': 'Strasbourg',
                 'country': 'FR',
                 'postalCode': '67000',
                 'street1': '2 rue de Rome',
                 'street2': 'Appt X'}
             }, subscriber['signatory'])

    def test_slimpay_api_create_order(self):
        euro = self.env['res.currency'].search([('name', '=', 'EUR')])
        with patch.object(slimpay_utils, 'get_client'):
            client = slimpay_utils.SlimpayClient('api_url', 'creditor',
                                                 'app_id', 'app_secret')
        subscriber = slimpay_utils.subscriber_from_partner(self.partner)
        result = client._repr_order(
            'tx', 'so', 'fr', 149.20000000000002, euro.name,
            euro.decimal_places, subscriber, 'https://commown.fr/')
        self.assertEqual('tx', result['reference'])
        self.assertEqual('fr', result['locale'])
        self.assertEqual(['signMandate', 'payment'],
                         [item['type'] for item in result['items']])
        sign, payment = result['items']
        self.assertIn('signatory', sign['mandate'])
        self.assertEqual(149.20, payment['payin']['amount'])
        self.assertEqual('so', payment['payin']['label'])
        self.assertEqual('EUR', payment['payin']['currency'])
        self.assertEqual('https://commown.fr/', payment['payin']['notifyUrl'])
