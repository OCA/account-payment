from odoo.tests.common import TransactionCase


class TestPaymentSelectCost(TransactionCase):

    def setUp(self):
        super(TestPaymentSelectCost, self).setUp()
        self.account_cost = self.env['account.account'].search([
            ('user_type_id', '=', self.env.ref('account.data_account_type_expenses').id)
        ], limit=1)
        self.bank_journal = self.env['account.journal'].create(
            {'name': 'Bank', 'type': 'bank', 'code': 'BNK'})

    def test_outbound_payment(self):
        payment = self.env['account.payment'].create({
            'payment_type': 'outbound',
            'partner_type': 'supplier',
            'journal_id': self.bank_journal.id,
            'payment_method_id': self.bank_journal.outbound_payment_method_ids[0].id,
            'amount': 100,
        })
        payment.onchange_destination_account_id()
        payment._convert_to_write(payment._cache)
        payment.force_destination_account_id = self.account_cost.id
        payment.post()
        self.assertEqual(len(payment.move_line_ids), 2)
        for line in payment.move_line_ids:
            if line.debit:
                self.assertEqual(line.account_id.id, self.account_cost.id)
