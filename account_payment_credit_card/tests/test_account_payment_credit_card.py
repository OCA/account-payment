# -*- coding: utf-8 -*-
# Copyright 2018 Bogdan Stanciu <bogdanovidiu.stanciu@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.addons.account.tests.account_test_classes \
    import AccountingTestCase


class TestAccountPaymentCreditCard(AccountingTestCase):

    def setUp(self):
        super(TestAccountPaymentCreditCard, self).setUp()
        self.register_payments_model = self.env['account.register.payments']
        self.payment_model = self.env['account.payment']
        self.invoice_model = self.env['account.invoice']
        self.invoice_line_model = self.env['account.invoice.line']
        self.acc_bank_stmt_model = self.env['account.bank.statement']
        self.acc_bank_stmt_line_model = self.env['account.bank.statement.line']

        self.partner_supplier = self.env.ref("base.res_partner_12")
        self.product = self.env.ref("product.product_product_4")
        self.payment_method_manual_in = self.env.ref(
            "account.account_payment_method_manual_in")
        self.payment_method_manual_out = self.env.ref(
            "account.account_payment_method_manual_out")

        self.account_receivable = self.env['account.account'].search([(
            'user_type_id', '=', self.env.ref(
                'account.data_account_type_receivable').id)], limit=1)
        self.account_payable = self.env['account.account'].search([(
            'user_type_id', '=', self.env.ref(
                'account.data_account_type_payable').id)], limit=1)
        self.account_revenue = self.env['account.account'].search([(
            'user_type_id', '=', self.env.ref(
                'account.data_account_type_revenue').id)], limit=1)
        self.account_expenses = self.env['account.account'].search([(
            'user_type_id', '=', self.env.ref(
                'account.data_account_type_expenses').id)], limit=1)

        type_current_assets = self.env.ref(
            'account.data_account_type_current_assets')

        self.account_credit_card = self.env['account.account'].create({
            'name': 'Credit card',
            'code': 'XX_1030',
            'user_type_id': type_current_assets.id,
        })
        self.card_issuer = self.env['res.partner'].create({
            'name': 'Test card issuer',
            'supplier': True,
        })
        self.journal_credit_card = self.env['account.journal'].create({
            'name': 'Test credit card payments',
            'type': 'bank',
            'code': 'TCC',
            'default_debit_account_id': self.account_credit_card.id,
            'default_credit_account_id': self.account_credit_card.id,
            'credit_card': True,
            'partner_id': self.card_issuer.id,
        })

    def create_invoice(
            self, amount=100, type_inv='out_invoice', currency_id=None):
        """ Returns an open invoice """
        invoice = self.invoice_model.create({
            'partner_id': self.partner_supplier.id,
            'reference_type': 'none',
            'name': type_inv == 'out_invoice' and 'invoice to client' or
            'invoice to supplier',
            'account_id': type_inv == 'out_invoice' and
            self.account_receivable.id or self.account_payable.id,
            'type': type,
            'journal_id': self.journal_purchase.id,
        })
        self.invoice_line_model.create({
            'product_id': self.product.id,
            'quantity': 1,
            'price_unit': amount,
            'invoice_id': invoice.id,
            'name': 'something',
            'account_id': self.account_expenses.id,
        })
        invoice.signal_workflow('invoice_open')
        return invoice

    def test_payment_journal_credit_card(self):
        payment = self.payment_model.create({
            'payment_type': 'outbound',
            'amount': 100,
            'journal_id': self.journal_credit_card.id,
            'partner_type': 'supplier',
            'partner_id': self.partner_supplier.id,
            'payment_method_id': self.payment_method_manual_out.id,
        })
        payment.post()
