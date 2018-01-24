from odoo.tests.common import TransactionCase


class PaymentModelTC(TransactionCase):

    def setUp(self):
        super(PaymentModelTC, self).setUp()
        self.slimpay = self.env['payment.acquirer'].search(
            [('provider', '=', 'slimpay')])
        self.slimpay.ensure_one()
        self.partner = self.env['res.partner'].create({'name': 'Commown'})

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

    def test_slimpay_signatory(self):
        self.assertEqual(
            {'familyName': u'Commown', 'email': None, 'givenName': None,
             'billingAddress': {'city': None,
                                'country': None,
                                'postalCode': None,
                                'street1': None,
                                'street2': None,
                                'telephone': None}
             }, self.slimpay.slimpay_signatory(self.partner))
        france = self.env['res.country'].search([('name', '=', 'France')])
        self.partner.write({'street': '2 rue de Rome', 'street2': 'Appt X',
                            'zip': '67000', 'city': 'Strasbourg',
                            'country_id': france.id})
        self.assertEqual(
            {'familyName': u'Commown', 'email': None, 'givenName': None,
             'billingAddress': {'city': u'Strasbourg',
                                'country': u'FR',
                                'postalCode': u'67000',
                                'street1': u'2 rue de Rome',
                                'street2': u'Appt X',
                                'telephone': None}
             }, self.slimpay.slimpay_signatory(self.partner))
