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
