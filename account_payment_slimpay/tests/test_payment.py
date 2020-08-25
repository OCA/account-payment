from mock import patch

from odoo.addons.payment_slimpay.models.payment import SlimpayClient

from odoo.tests.common import TransactionCase, at_install, post_install


@at_install(False)
@post_install(True)
class SlimpayPaymentTC(TransactionCase):

    def setUp(self):
        patcher = patch('odoo.addons.payment_slimpay.models.'
                        'slimpay_utils.get_client')
        patcher.start()
        super(SlimpayPaymentTC, self).setUp()
        self.addCleanup(patcher.stop)

        self.partner = self.env.ref('base.res_partner_2')
        slimpay = self.env['payment.acquirer'].search(
            [('provider', '=', 'slimpay')]).ensure_one()
        self.token = self.env['payment.token'].create({
            'name': 'Test Slimpay Token', 'partner_id': self.partner.id,
            'active': True, 'acquirer_id': slimpay.id,
            'acquirer_ref': 'Slimpay mandate ref',
        })

    def test_s2s_do_translation(self):
        euro = self.env['res.currency'].search([('name', '=', 'EUR')])
        tx = self.env['payment.transaction'].create({
            'reference': 'TEST', 'acquirer_id': self.token.acquirer_id.id,
            'payment_token_id': self.token.id, 'amount': 149.20000000000002,
            'state': 'draft', 'currency_id': euro.id,
            'partner_id': self.partner.id, 'partner_email': self.partner.email,
            'partner_country_id': self.partner.country_id.id,
            'partner_city': self.partner.city, 'partner_zip': self.partner.zip,
        })

        def fake_action(method, func, params=None):
            if method == 'GET' and func == 'get-mandates':
                self.assertEqual(params['id'], self.token.acquirer_ref)
                return {'reference': 'MANDATE_REF'}
            elif method == 'POST' and func == 'create-payins':
                self.assertEqual(params['mandate']['reference'], 'MANDATE_REF')
                self.assertEqual(params['amount'], 149.2)  # rounded amount
                return {'executionStatus': 'toprocess', 'state': 'accepted',
                        'reference': 'PAYIN_REF'}

        with patch.object(SlimpayClient, 'action', side_effect=fake_action):
            tx.slimpay_s2s_do_transaction()
        self.assertEqual(tx.state, 'done')
        self.assertEqual(tx.acquirer_reference, 'PAYIN_REF')
