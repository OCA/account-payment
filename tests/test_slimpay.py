from odoo.tests.common import TransactionCase


class PaymentModelTC(TransactionCase):

    def setUp(self):
        super(PaymentModelTC, self).setUp()
        self.slimpay = self.env['payment.acquirer'].search(
            [('provider', '=', 'slimpay')])
        self.slimpay.ensure_one()
        france = self.env['res.country'].search([('name', '=', 'France')])
        self.partner = self.env['res.partner'].create(
            {'name': 'Commown', 'country_id': france.id})

    def check_phone_value(self, expected):
        actual = self.slimpay.slimpay_mobile_phone(self.partner)
        if expected is None:
            self.assertIsNone(actual)
        else:
            self.assertEqual(expected, actual)

    def test_slimpay_mobile_phone(self):
        self.partner.write({'phone': None})
        self.check_phone_value(None)
        self.partner.write({'phone': '06.01.02.03.04'})
        self.check_phone_value('+33601020304')

    def test_slimpay_api_signatory(self):
        self.assertEqual(
            {'familyName': u'Commown', 'email': None, 'givenName': None,
             'telephone': None, 'billingAddress': {
                 'city': None,
                 'country': u'FR',
                 'postalCode': None,
                 'street1': None,
                 'street2': None}
             }, self.slimpay._slimpay_api_signatory(self.partner))
        self.partner.write({'street': '2 rue de Rome', 'street2': 'Appt X',
                            'zip': '67000', 'city': 'Strasbourg'})
        self.assertEqual(
            {'familyName': u'Commown', 'email': None, 'givenName': None,
             'telephone': None, 'billingAddress': {
                 'city': u'Strasbourg',
                 'country': u'FR',
                 'postalCode': u'67000',
                 'street1': u'2 rue de Rome',
                 'street2': u'Appt X'}
             }, self.slimpay._slimpay_api_signatory(self.partner))

    def test_slimpay_api_create_order(self):
        euro = self.env['res.currency'].search([('name', '=', 'EUR')])
        result = self.slimpay._slimpay_api_create_order(
            'my ref', 42, euro, self.partner, 'https://commown.fr/')
        self.assertEqual('my ref', result['reference'])
        self.assertEqual('fr', result['locale'])
        self.assertEqual(['signMandate', 'payment'],
                         [item['type'] for item in result['items']])
        sign, payment = result['items']
        self.assertIn('signatory', sign['mandate'])
        self.assertEqual(42, payment['payin']['amount'])
        self.assertEqual(u'EUR', payment['payin']['currency'])
        self.assertEqual('https://commown.fr/', payment['payin']['notifyUrl'])
