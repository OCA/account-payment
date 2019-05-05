# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo.tests.common import SavepointCase
from odoo.tests.common import Form


class TestPaymentMultiDeduction(SavepointCase):

    @classmethod
    def setUpClass(self):
        super(TestPaymentMultiDeduction, self).setUpClass()

        self.account_receivable = self.env['account.account'].search(
            [('user_type_id', '=', self.env.ref(
                'account.data_account_type_receivable').id)], limit=1)
        self.account_payable = self.env['account.account'].search(
            [('user_type_id', '=', self.env.ref(
                'account.data_account_type_payable').id)], limit=1)
        self.account_revenue = self.env['account.account'].search(
            [('user_type_id', '=', self.env.ref(
                'account.data_account_type_revenue').id)], limit=1)
        self.account_expense = self.env['account.account'].search(
            [('user_type_id', '=', self.env.ref(
                'account.data_account_type_expenses').id)], limit=1)

        self.cust_invoice_1 = self.env['account.invoice'].create({
            'name': "Test Customer Invoice",
            'journal_id': self.env['account.journal'].search(
                [('type', '=', 'sale')], limit=1).id,
            'partner_id': self.env.ref('base.res_partner_12').id,
            'account_id': self.account_receivable.id,
            'invoice_line_ids': [
                (0, 0, {
                    'product_id': self.env.ref('product.product_product_3').id,
                    'quantity': 1.0,
                    'account_id': self.account_revenue.id,
                    'name': '[PCSC234] PC Assemble SC234',
                    'price_unit': 450.00
                    })
            ],
        })

        self.cust_invoice_2 = self.cust_invoice_1.copy()

    def test_1_one_invoice_payment(self):
        """ Validate 1 invoice and make payment with 2 deduction """
        self.cust_invoice_1.action_invoice_open()  # total amount 450.0
        ctx = {'active_ids': [self.cust_invoice_1.id],
               'active_id': self.cust_invoice_1.id,
               'active_model': 'account.invoice'}
        PaymentWizard = self.env['account.payment']
        view_id = ('account_payment_multi_deduction.'
                   'view_account_payment_invoice_form')
        with Form(PaymentWizard.with_context(ctx), view=view_id) as f:
            f.amount = 400.0  # Reduce to 400.0, and mark fully paid (multi)
            f.payment_difference_handling = 'reconcile_multi_deduct'
            with f.deduction_ids.new() as f2:
                f2.account_id = self.account_expense
                f2.name = 'Expense 1'
                f2.amount = 20.0
            with f.deduction_ids.new() as f2:
                f2.account_id = self.account_expense
                f2.name = 'Expense 2'
                f2.amount = 30.0
        payment = f.save()
        payment.action_validate_invoice_payment()

        self.assertEqual(payment.state, 'posted')

        move_lines = self.env['account.move.line'].search(
            [('payment_id', '=', payment.id)])
        bank_account = payment.journal_id.default_debit_account_id or \
            payment.journal_id.default_credit_account_id

        self.assertEqual(self.cust_invoice_1.state, 'paid')

        self.assertRecordValues(move_lines, [
            {'account_id': bank_account.id,
             'debit': 400.0, 'credit': 0.0},
            {'account_id': self.account_expense.id, 'name': 'Expense 2',
             'debit': 30.0, 'credit': 0.0},
            {'account_id': self.account_expense.id, 'name': 'Expense 1',
             'debit': 20.0, 'credit': 0.0},
            {'account_id': self.account_receivable.id,
             'debit': 0.0, 'credit': 450.0},
        ])

    def test_2_two_invoices_register_payment(self):
        """ Validate 2 invoice and make payment on both with 2 deduction """
        self.cust_invoice_1.action_invoice_open()  # Total 900.0 = 450 + 450
        self.cust_invoice_2.action_invoice_open()
        ctx = {'active_ids': [self.cust_invoice_1.id,
                              self.cust_invoice_2.id],
               'active_model': 'account.invoice'}
        PaymentWizard = self.env['account.register.payments']
        view_id = ('account_payment_multi_deduction.'
                   'view_account_payment_from_invoices')
        with Form(PaymentWizard.with_context(ctx), view=view_id) as f:
            f.amount = 600.0  # Reduce to 600.0, and mark fully paid (multi)
            f.payment_difference_handling = 'reconcile_multi_deduct'
            with f.deduction_ids.new() as f2:
                f2.account_id = self.account_expense
                f2.name = 'Expense 1'
                f2.amount = 100.0
            with f.deduction_ids.new() as f2:
                f2.account_id = self.account_expense
                f2.name = 'Expense 2'
                f2.amount = 200.0
        register_payment = f.save()
        vals = register_payment.create_payments()
        payment = self.env['account.payment'].browse(vals.get('res_id'))

        self.assertEqual(payment.state, 'posted')

        move_lines = self.env['account.move.line'].search(
            [('payment_id', '=', payment.id)])
        bank_account = payment.journal_id.default_debit_account_id or \
            payment.journal_id.default_credit_account_id

        self.assertEqual(self.cust_invoice_1.state, 'paid')
        self.assertEqual(self.cust_invoice_2.state, 'paid')

        self.assertRecordValues(move_lines, [
            {'account_id': bank_account.id,
             'debit': 600.0, 'credit': 0.0},
            {'account_id': self.account_expense.id, 'name': 'Expense 2',
             'debit': 200.0, 'credit': 0.0},
            {'account_id': self.account_expense.id, 'name': 'Expense 1',
             'debit': 100.0, 'credit': 0.0},
            {'account_id': self.account_receivable.id,
             'debit': 0.0, 'credit': 900.0},
        ])
