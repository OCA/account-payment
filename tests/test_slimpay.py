from odoo.tests.common import TransactionCase

from odoo.addons.payment_slimpay.models import slimpay_utils


class SlimpayUtilsTC(TransactionCase):

    def setUp(self):
        super(SlimpayUtilsTC, self).setUp()
        france = self.env['res.country'].search([('name', '=', 'France')])
        self.partner = self.env['res.partner'].create(
            {'name': 'Commown', 'country_id': france.id})

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
            {'familyName': u'Commown', 'email': None, 'givenName': None,
             'telephone': None, 'billingAddress': {
                 'city': None,
                 'country': u'FR',
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
            {'familyName': u'Commown', 'email': None, 'givenName': None,
             'telephone': None, 'billingAddress': {
                 'city': u'Strasbourg',
                 'country': u'FR',
                 'postalCode': u'67000',
                 'street1': u'2 rue de Rome',
                 'street2': u'Appt X'}
             }, subscriber['signatory'])

    def test_slimpay_api_create_order(self):
        euro = self.env['res.currency'].search([('name', '=', 'EUR')])
        client = slimpay_utils.SlimpayClient('api_url', 'creditor',
                                             'app_id', 'app_secret')
        subscriber = slimpay_utils.subscriber_from_partner(self.partner)
        result = client._repr_order(
            'my ref', 'fr', 42, euro.name, subscriber, 'https://commown.fr/')
        self.assertEqual('my ref', result['reference'])
        self.assertEqual('fr', result['locale'])
        self.assertEqual(['signMandate', 'payment'],
                         [item['type'] for item in result['items']])
        sign, payment = result['items']
        self.assertIn('signatory', sign['mandate'])
        self.assertEqual(42, payment['payin']['amount'])
        self.assertEqual(u'EUR', payment['payin']['currency'])
        self.assertEqual('https://commown.fr/', payment['payin']['notifyUrl'])
