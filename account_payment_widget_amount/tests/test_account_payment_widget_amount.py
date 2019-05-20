# Copyright 2017 Eficent Business and IT Consulting Services, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase
import time


class TestAccountPaymentWidgetAmount(TransactionCase):

    def setUp(self):
        super(TestAccountPaymentWidgetAmount, self).setUp()
        # Models
        self.partner = self.env['res.partner'].create({'name': 'Test'})
        self.account_account_type_model = self.env['account.account.type']
        self.account_account_model = self.env['account.account']
        self.account_payment_model = self.env['account.payment']
        self.account_journal_model = self.env['account.journal']
        self.account_invoice_model = self.env['account.invoice']
        self.account_move_line_model = self.env['account.move.line']
        self.invoice_line_model = self.env['account.invoice.line']
        # Records
        self.company = self.env.ref('base.main_company')

        self.account_type_bank = self.account_account_type_model.create({
            'name': 'Test Bank',
            'type': 'liquidity',
        })
        self.account_type_receivable = self.account_account_type_model.create({
            'name': 'Test Receivable',
            'type': 'receivable',
        })
        self.account_type_payable = self.account_account_type_model.create({
            'name': 'Test Payable',
            'type': 'receivable',
        })
        self.account_type_regular = self.account_account_type_model.create({
            'name': 'Test Regular',
            'type': 'other',
        })
        self.account_bank = self.account_account_model.create({
            'name': 'Test Bank',
            'code': 'TEST_BANK',
            'user_type_id': self.account_type_bank.id,
            'reconcile': False,
            'company_id': self.company.id,
        })
        self.account_receivable = self.account_account_model.create({
            'name': 'Test Receivable',
            'code': 'TEST_AR',
            'user_type_id': self.account_type_receivable.id,
            'reconcile': True,
            'company_id': self.company.id,
        })
        self.account_payable = self.account_account_model.create({
            'name': 'Test Payable',
            'code': 'TEST_AP',
            'user_type_id': self.account_type_payable.id,
            'reconcile': True,
            'company_id': self.company.id,
        })
        self.partner.property_account_receivable_id = self.account_receivable
        self.partner.property_account_payable_id = self.account_payable
        self.account_income = self.account_account_model.create({
            'name': 'Test Income',
            'code': 'TEST_IN',
            'user_type_id': self.account_type_regular.id,
            'reconcile': False,
            'company_id': self.company.id,
        })
        self.account_expense = self.account_account_model.create({
            'name': 'Test Expense',
            'code': 'TEST_EX',
            'user_type_id': self.account_type_regular.id,
            'reconcile': False,
            'company_id': self.company.id,
        })
        self.bank_journal = self.account_journal_model.create({
            'name': 'Test Bank',
            'code': 'TBK',
            'type': 'bank',
            'company_id': self.company.id,
        })
        self.sale_journal = self.account_journal_model.\
            search([('type', '=', 'sale'),
                    ('company_id', '=', self.company.id)])[0]
        self.purchase_journal = self.account_journal_model. \
            search([('type', '=', 'purchase'),
                    ('company_id', '=', self.company.id)])[0]
        # Create a new currency. It is 2x the valuation
        # of the company currency.
        self.new_usd = self.env['res.currency'].create({
            'name': 'us2',
            'symbol': '$²',
            'rate_ids': [(0, 0, {'rate': 2,
                                 'name': time.strftime('%Y-%m-%d')})],
        })

    def test_01(self):
        """ Tests that I can create an invoice in company currency,
        register a payment in company currency, and then reconcile part
        of the payment to the invoice.
        I expect:
        - The residual amount of the invoice is reduced by the amount assigned.
        - The residual amount of the payment is reduced by the amount assigned.
        """
        invoice = self.account_invoice_model.create({
            'name': "Test Customer Invoice",
            'journal_id': self.sale_journal.id,
            'partner_id': self.partner.id,
            'account_id': self.account_receivable.id,
            'company_id': self.company.id,
            'currency_id': self.company.currency_id.id,
        })

        self.invoice_line_model.create({
            'invoice_id': invoice.id,
            'name': 'Line 1',
            'price_unit': 200.0,
            'account_id': self.account_income.id,
            'quantity': 1,
            'company_id': self.company.id,
        })
        # Open invoice
        invoice.action_invoice_open()
        # Create a payment
        payment = self.account_payment_model.create(
            {'payment_type': 'inbound',
             'payment_method_id':
                self.env.ref('account.account_payment_method_manual_in').id,
             'partner_type': 'customer',
             'partner_id': self.partner.id,
             'amount': 1000.0,
             'currency_id': self.company.currency_id.id,
             'payment_date': time.strftime('%Y-%m-%d'),
             'journal_id': self.bank_journal.id,
             'company_id': self.company.id,
             })
        payment.post()
        payment_ml = payment.move_line_ids.filtered(
            lambda l: l.account_id == self.account_receivable)
        invoice.with_context(paid_amount=100.0).assign_outstanding_credit(
            payment_ml.id)
        self.assertEqual(invoice.residual, 100.0)
        self.assertFalse(payment.move_reconciled)
        invoice.with_context(paid_amount=100.0).assign_outstanding_credit(
            payment_ml.id)
        self.assertEqual(invoice.residual, 0.0)
        self.assertEqual(invoice.state, 'paid')
        self.assertFalse(payment.move_reconciled)

    def test_02(self):
        """ Tests that I can create an invoice in foreign currency,
        register a payment in company currency, and then reconcile part
        of the payment to the invoice.
        I expect:
        - The residual amount of the invoice is reduced by the amount assigned.
        - The residual amount of the payment is reduced by the amount assigned.
        """
        self.company.currency_id.rate_ids = False
        # The invoice is for 200 in the new currency, which translates in 100
        # in company currency.
        invoice = self.account_invoice_model.create({
            'name': "Test Customer Invoice",
            'journal_id': self.sale_journal.id,
            'partner_id': self.partner.id,
            'account_id': self.account_receivable.id,
            'company_id': self.company.id,
            'currency_id': self.new_usd.id,
        })

        self.invoice_line_model.create({
            'invoice_id': invoice.id,
            'name': 'Line 1',
            'price_unit': 200.0,
            'account_id': self.account_income.id,
            'quantity': 1,
            'company_id': self.company.id,
        })
        # Open invoice
        invoice.action_invoice_open()
        # Create a payment
        payment = self.account_payment_model.create(
            {'payment_type': 'inbound',
             'payment_method_id':
                self.env.ref('account.account_payment_method_manual_in').id,
             'partner_type': 'customer',
             'partner_id': self.partner.id,
             'amount': 1000.0,
             'currency_id': self.company.currency_id.id,
             'payment_date': time.strftime('%Y-%m-%d'),
             'journal_id': self.bank_journal.id,
             'company_id': self.company.id,
             })
        payment.post()
        payment_ml = payment.move_line_ids.filtered(
            lambda l: l.account_id == self.account_receivable)
        # We pay 100 in the currency of the invoice. Which means that in
        # company currency we are paying 50.
        invoice.with_context(paid_amount=100.0).assign_outstanding_credit(
            payment_ml.id)
        self.assertEqual(invoice.residual_signed, 100.0)
        self.assertEqual(invoice.state, 'open')
        self.assertFalse(payment.move_reconciled)
        self.assertEqual(payment_ml.amount_residual, -950.0)

    def test_03(self):
        """ Tests that I can create an refund invoice in foreign currency,
        register an outgoing payment in company currency, and then
        reconcile part of the payment to the invoice.
        I expect:
        - The residual amount of the invoice is reduced by the amount assigned.
        - The residual amount of the payment is reduced by the amount assigned.
        """
        self.company.currency_id.rate_ids = False
        # The invoice is for 200 in the new currency, which translates in 100
        # in company currency.
        invoice = self.account_invoice_model.create({
            'name': "Test Customer Invoice",
            'type': "out_refund",
            'journal_id': self.sale_journal.id,
            'partner_id': self.partner.id,
            'account_id': self.account_receivable.id,
            'company_id': self.company.id,
            'currency_id': self.new_usd.id,
        })

        self.invoice_line_model.create({
            'invoice_id': invoice.id,
            'name': 'Line 1',
            'price_unit': 200.0,
            'account_id': self.account_income.id,
            'quantity': 1,
            'company_id': self.company.id,
        })
        # Open invoice
        invoice.action_invoice_open()
        # Create a payment
        payment = self.account_payment_model.create(
            {'payment_type': 'outbound',
             'payment_method_id':
                self.env.ref('account.account_payment_method_manual_out').id,
             'partner_type': 'customer',
             'partner_id': self.partner.id,
             'amount': 1000.0,
             'currency_id': self.company.currency_id.id,
             'payment_date': time.strftime('%Y-%m-%d'),
             'journal_id': self.bank_journal.id,
             'company_id': self.company.id,
             })
        payment.post()
        payment_ml = payment.move_line_ids.filtered(
            lambda l: l.account_id == self.account_receivable)
        # We collect 100 in the currency of the refund. Which means that in
        # company currency we are reconciling 50.
        invoice.with_context(paid_amount=100.0).assign_outstanding_credit(
            payment_ml.id)
        self.assertEqual(invoice.residual_signed, -100.0)
        self.assertEqual(invoice.state, 'open')
        self.assertFalse(payment.move_reconciled)
        self.assertEqual(payment_ml.amount_residual, 950.0)

    def test_04(self):
        """ Tests that I can create an invoice in company currency,
        register a payment in foreign currency, and then reconcile part
        of the payment to the invoice.
        I expect:
        - The residual amount of the invoice is reduced by the amount assigned.
        - The residual amount of the payment is reduced by the amount assigned.
        """
        self.company.currency_id.rate_ids = False
        invoice = self.account_invoice_model.create({
            'name': "Test Customer Invoice",
            'journal_id': self.sale_journal.id,
            'partner_id': self.partner.id,
            'account_id': self.account_receivable.id,
            'company_id': self.company.id,
            'currency_id': self.company.currency_id.id,
        })

        self.invoice_line_model.create({
            'invoice_id': invoice.id,
            'name': 'Line 1',
            'price_unit': 200.0,
            'account_id': self.account_income.id,
            'quantity': 1,
            'company_id': self.company.id,
        })
        # Open invoice
        invoice.action_invoice_open()
        # Create a payment for 1000 of foreign currency, which translates
        # to 500 in company currency.
        payment = self.account_payment_model.create(
            {'payment_type': 'inbound',
             'payment_method_id':
                self.env.ref('account.account_payment_method_manual_in').id,
             'partner_type': 'customer',
             'partner_id': self.partner.id,
             'amount': 1000.0,
             'currency_id': self.new_usd.id,
             'payment_date': time.strftime('%Y-%m-%d'),
             'journal_id': self.bank_journal.id,
             'company_id': self.company.id,
             })
        payment.post()
        payment_ml = payment.move_line_ids.filtered(
            lambda l: l.account_id == self.account_receivable)
        # We pay 100 in the currency of the invoice, which is the
        # company currency
        invoice.with_context(paid_amount=100.0).assign_outstanding_credit(
            payment_ml.id)
        self.assertEqual(invoice.residual_signed, 100.0)
        self.assertEqual(invoice.state, 'open')
        self.assertFalse(payment.move_reconciled)
        self.assertEqual(payment_ml.amount_residual, -400.0)
        self.assertEqual(payment_ml.amount_residual_currency, -800.0)
        invoice.with_context(paid_amount=100.0).assign_outstanding_credit(
            payment_ml.id)
        self.assertEqual(invoice.residual_signed, 0.0)
        self.assertEqual(invoice.state, 'paid')
        self.assertEqual(payment_ml.amount_residual, -300.0)
        self.assertEqual(payment_ml.amount_residual_currency, -600.0)

    def test_05(self):
        """ Tests that I can create a vendor bill in company currency,
        register a payment in company currency, and then reconcile part
        of the payment to the bill.
        I expect:
        - The residual amount of the invoice is reduced by the amount assigned.
        - The residual amount of the payment is reduced by the amount assigned.
        """
        invoice = self.account_invoice_model.create({
            'name': "Test Vendor Bill",
            'type': 'in_invoice',
            'journal_id': self.purchase_journal.id,
            'partner_id': self.partner.id,
            'account_id': self.account_payable.id,
            'company_id': self.company.id,
            'currency_id': self.company.currency_id.id,
        })

        self.invoice_line_model.create({
            'invoice_id': invoice.id,
            'name': 'Line 1',
            'price_unit': 200.0,
            'account_id': self.account_expense.id,
            'quantity': 1,
            'company_id': self.company.id,
        })
        # Open invoice
        invoice.action_invoice_open()
        # Create a payment
        payment = self.account_payment_model.create(
            {'payment_type': 'outbound',
             'payment_method_id':
                self.env.ref('account.account_payment_method_manual_out').id,
             'partner_type': 'supplier',
             'partner_id': self.partner.id,
             'amount': 1000.0,
             'currency_id': self.company.currency_id.id,
             'payment_date': time.strftime('%Y-%m-%d'),
             'journal_id': self.bank_journal.id,
             'company_id': self.company.id,
             })
        payment.post()
        payment_ml = payment.move_line_ids.filtered(
            lambda l: l.account_id == self.account_payable)
        invoice.with_context(paid_amount=100.0).assign_outstanding_credit(
            payment_ml.id)
        self.assertEqual(invoice.residual, 100.0)
        self.assertFalse(payment.move_reconciled)
        invoice.with_context(paid_amount=100.0).assign_outstanding_credit(
            payment_ml.id)
        self.assertEqual(invoice.residual, 0.0)
        self.assertEqual(invoice.state, 'paid')
        self.assertFalse(payment.move_reconciled)
