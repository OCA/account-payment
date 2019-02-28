# -*- coding: utf-8 -*-

from odoo import fields
from odoo.addons.account.tests.account_test_classes import AccountingTestCase
from datetime import date


class TestAccountInvoiceNegative(AccountingTestCase):

    def setUp(self):
        super(TestAccountInvoiceNegative, self).setUp()
        self.payment_model = self.env['account.payment']
        self.register_payments_model = self.env['account.register.payments']
        self.payment_method_model = self.env['account.payment.method']
        self.payment_method_check = self.payment_method_model.search(
            [('code', '=', 'check_printing')], limit=1,
        )
        if not self.payment_method_check:
            self.payment_method_check = self.payment_method_model.create({
                'name': 'Check',
                'code': 'check_printing',
                'payment_type': 'outbound',
                'check': True,
            })
        self.account_user_type = self.env.\
            ref('account.data_account_type_receivable')
        self.account_user_type_payable = self.env. \
            ref('account.data_account_type_payable')
        self.revenue_user_type = self.env.\
            ref('account.data_account_type_revenue')
        self.expense_user_type = self.env. \
            ref('account.data_account_type_expenses')
        self.account = self.env['account.account']
        self.account_move_line_model = self.env['account.move.line']
        self.account_invoice_model = self.env['account.invoice']
        self.account_invoice_line_model = self.env['account.invoice.line']
        self.partner_agrolait = self.env.ref('base.res_partner_2')
        self.partner_delta = self.env.ref('base.res_partner_4')
        self.currency_usd = self.env.ref('base.USD')
        self.payment_term = self.env.ref('account.account_payment_term_15days')
        self.product = self.env.ref('product.product_product_4')
        self.company = self.env.ref('base.main_company')
        self._create_account_type()
        self.bank_journal = self.env['account.journal'].create(
            {'name': 'Bank US', 'type': 'bank', 'code': 'BNKNI',
             'currency_id': self.currency_usd.id})
        # we create an invoice
        inv_date = date.today()
        self.invoice = self.account_invoice_model.create({
            'partner_id': self.partner_agrolait.id,
            'reference_type': 'none',
            'currency_id': self.currency_usd.id,
            'name': 'invoice to customer',
            'payment_term_id': self.payment_term.id,
            'account_id': self.receivable_account.id,
            'type': 'out_invoice',
            'date_invoice': fields.Date.to_string(inv_date)})

        self.account_invoice_line_model.create({
            'product_id': self.product.id,
            'quantity': 1,
            'price_unit': 100.0,
            'account_id': self.sales_account.id,
            'invoice_id': self.invoice.id,
            'name': 'product that cost -100'})
        self.invoice.action_invoice_open()
        # we create a negative invoice
        self.negative_invoice = self.account_invoice_model.create({
            'partner_id': self.partner_agrolait.id,
            'reference_type': 'none',
            'currency_id': self.currency_usd.id,
            'name': 'invoice to customer',
            'payment_term_id': self.payment_term.id,
            'account_id': self.receivable_account.id,
            'type': 'out_invoice',
            'date_invoice': fields.Date.to_string(inv_date)})

        self.account_invoice_line_model.create({
            'product_id': self.product.id,
            'quantity': 1,
            'price_unit': -100.0,
            'account_id': self.sales_account.id,
            'invoice_id': self.negative_invoice.id,
            'name': 'product that cost -100'})

        # create a supplier invoice
        self.supplier_invoice = self.account_invoice_model.create({
            'partner_id': self.partner_delta.id,
            'reference_type': 'none',
            'currency_id': self.currency_usd.id,
            'name': 'invoice to supplier',
            'payment_term_id': self.payment_term.id,
            'account_id': self.payable_account.id,
            'type': 'in_invoice',
            'date_invoice': fields.Date.to_string(inv_date)})
        self.account_invoice_line_model.create({
            'product_id': self.product.id,
            'quantity': 1,
            'price_unit': 100.0,
            'account_id': self.purchase_account.id,
            'invoice_id': self.supplier_invoice.id,
            'name': 'product that cost -100'})
        self.supplier_invoice.action_invoice_open()

        # we create a negative supplier invoice
        self.supplier_negative_invoice = self.account_invoice_model.create({
            'partner_id': self.partner_delta.id,
            'reference_type': 'none',
            'currency_id': self.currency_usd.id,
            'name': 'negative invoice to supplier',
            'payment_term_id': self.payment_term.id,
            'account_id': self.payable_account.id,
            'type': 'in_invoice',
            'date_invoice': fields.Date.to_string(inv_date)})
        self.account_invoice_line_model.create({
            'product_id': self.product.id,
            'quantity': 1,
            'price_unit': -100.0,
            'account_id': self.purchase_account.id,
            'invoice_id': self.supplier_negative_invoice.id,
            'name': 'product that cost -100'})

    def _create_account_type(self):
        # Create receivable and sales test account
        self.receivable_account = self.account.create({
            'name': 'Recv - Test',
            'code': 'test_recv',
            'user_type_id': self.account_user_type.id,
            'company_id': self.company.id,
            'reconcile': True
        })
        self.sales_account = self.account.create({
            'name': 'Local Sales - Test',
            'code': 'test_sales',
            'user_type_id': self.revenue_user_type.id,
            'company_id': self.company.id,
        })
        self.payable_account = self.account.create({
            'name': 'Pay - Test',
            'code': 'test_pay',
            'user_type_id': self.account_user_type_payable.id,
            'company_id': self.company.id,
            'reconcile': True
        })
        self.purchase_account = self.account.create({
            'name': 'Local Purchases - Test',
            'code': 'test_purch',
            'user_type_id': self.expense_user_type.id,
            'company_id': self.company.id,
        })

    def test_1_positive_invoice_payment(self):
        self.assertAlmostEquals(self.invoice.amount_total, 100.0)
        self.assertAlmostEquals(self.invoice.residual, 100)
        ctx = {'active_model': 'account.invoice',
               'active_ids': [self.invoice.id]}
        register_payments = \
            self.register_payments_model.with_context(ctx).create({
                'payment_date': fields.Date.to_string(date.today()),
                'journal_id': self.bank_journal.id,
                'payment_method_id': self.payment_method_check.id
            })
        register_payments.create_payment()
        payment = self.payment_model.search([], order="id desc", limit=1)
        self.assertAlmostEquals(payment.amount, 100)
        self.assertAlmostEquals(payment.payment_difference, -100)
        self.assertEqual(payment.state, 'posted')
        self.assertEqual(self.invoice.state, 'paid')

        # rest refund invoice
        # I refund the invoice Using Refund Button
        invoice_refund_obj = self.env['account.invoice.refund']
        account_invoice_refund = invoice_refund_obj.create(dict(
            description='Refund invoice',
            date=fields.Date.to_string(date.today()),
            filter_refund='refund'
        ))

        # I clicked on refund button.
        account_invoice_refund.with_context({
            'active_ids': [self.invoice.id]
        }).invoice_refund()
        invoice_refund = self.env['account.invoice'].search(
            [], order='id desc', limit=1)
        invoice_refund.action_invoice_open()
        self.assertEqual(invoice_refund.amount_total, 100.0)
        self.assertAlmostEquals(invoice_refund.residual, 100)
        self.assertEqual(invoice_refund.type, 'out_refund')
        ctx1 = {'active_model': 'account.invoice',
                'active_ids': [invoice_refund.id]}
        refund_register_payments = \
            self.register_payments_model.with_context(ctx1).create({
                'payment_date': fields.Date.to_string(date.today()),
                'journal_id': self.bank_journal.id,
                'payment_method_id': self.payment_method_check.id
            })
        refund_register_payments.create_payment()
        refund_payment = self.payment_model.search(
            [], order="id desc", limit=1)
        self.assertAlmostEquals(refund_payment.amount, 100)
        self.assertAlmostEquals(refund_payment.payment_difference, 100)
        self.assertEqual(refund_payment.state, 'posted')
        self.assertEqual(invoice_refund.state, 'paid')

    def test_2_negative_invoice_payment(self):
        self.negative_invoice.action_invoice_open()
        self.assertEqual(self.negative_invoice.amount_total, -100.0)
        self.assertAlmostEquals(self.negative_invoice.residual, 100.0)
        ctx = {'active_model': 'account.invoice',
               'active_ids': [self.negative_invoice.id]}
        register_payments = \
            self.register_payments_model.with_context(ctx).create({
                'payment_date': fields.Date.to_string(date.today()),
                'journal_id': self.bank_journal.id,
                'payment_method_id': self.payment_method_check.id
            })
        register_payments.create_payment()
        payment = self.payment_model.search([], order="id desc", limit=1)
        self.assertAlmostEquals(payment.amount, 100)
        self.assertAlmostEquals(payment.payment_difference, 100)
        self.assertEqual(payment.state, 'posted')
        self.assertEqual(self.negative_invoice.state, 'paid')

        # rest refund negativeinvoice
        # I refund the invoice Using Refund Button
        invoice_refund_obj = self.env['account.invoice.refund']
        account_invoice_refund = invoice_refund_obj.create(dict(
            description='Refund invoice',
            date=fields.Date.to_string(date.today()),
            filter_refund='refund'
        ))

        # I clicked on refund button.
        account_invoice_refund.with_context({
            'active_ids': [self.negative_invoice.id]
        }).invoice_refund()
        invoice_refund = self.env['account.invoice'].search(
            [], order='id desc', limit=1)
        invoice_refund.action_invoice_open()
        self.assertEqual(invoice_refund.amount_total, -100.0)
        self.assertAlmostEquals(invoice_refund.residual, 100.0)
        self.assertEqual(invoice_refund.type, 'out_refund')
        ctx1 = {'active_model': 'account.invoice',
                'active_ids': [invoice_refund.id]}
        refund_register_payments = \
            self.register_payments_model.with_context(ctx1).create({
                'payment_date': fields.Date.to_string(date.today()),
                'journal_id': self.bank_journal.id,
                'payment_method_id': self.payment_method_check.id
            })
        refund_register_payments.create_payment()
        refund_payment = self.payment_model.search(
            [], order="id desc", limit=1)
        self.assertAlmostEquals(refund_payment.amount, 100)
        self.assertAlmostEquals(refund_payment.payment_difference, -100)
        self.assertEqual(refund_payment.state, 'posted')
        self.assertEqual(invoice_refund.state, 'paid')

    def test_3_positive_supplier_invoice_payment(self):
        self.assertAlmostEquals(self.supplier_invoice.amount_total, 100.0)
        self.assertAlmostEquals(self.supplier_invoice.residual, 100)
        ctx = {'active_model': 'account.invoice',
               'active_ids': [self.supplier_invoice.id]}
        register_payments = \
            self.register_payments_model.with_context(ctx).create({
                'payment_date': fields.Date.today(),
                'journal_id': self.bank_journal.id,
                'payment_method_id': self.payment_method_check.id
            })
        register_payments.create_payment()
        payment = self.payment_model.search([], order="id desc", limit=1)
        self.assertAlmostEquals(payment.amount, 100)
        self.assertAlmostEquals(payment.payment_difference, 100)
        self.assertEqual(payment.state, 'posted')
        self.assertEqual(self.supplier_invoice.state, 'paid')

        # rest refund invoice
        # I refund the invoice Using Refund Button
        invoice_refund_obj = self.env['account.invoice.refund']
        account_invoice_refund = invoice_refund_obj.create(dict(
            description='Refund invoice',
            date=fields.Date.today(),
            filter_refund='refund'
        ))

        # I clicked on refund button.
        account_invoice_refund.with_context({
            'active_ids': [self.supplier_invoice.id]
        }).invoice_refund()
        invoice_refund = self.env['account.invoice'].search(
            [], order='id desc', limit=1)
        invoice_refund.action_invoice_open()
        self.assertEqual(invoice_refund.amount_total, 100.0)
        self.assertAlmostEquals(invoice_refund.residual, 100)
        self.assertEqual(invoice_refund.type, 'in_refund')
        ctx1 = {'active_model': 'account.invoice',
                'active_ids': [invoice_refund.id]}
        refund_register_payments = \
            self.register_payments_model.with_context(ctx1).create({
                'payment_date': fields.Date.to_string(date.today()),
                'journal_id': self.bank_journal.id,
                'payment_method_id': self.payment_method_check.id
            })
        refund_register_payments.create_payment()
        refund_payment = self.payment_model.search(
            [], order="id desc", limit=1)
        self.assertAlmostEquals(refund_payment.amount, 100)
        self.assertAlmostEquals(refund_payment.payment_difference, -100)
        self.assertEqual(refund_payment.state, 'posted')
        self.assertEqual(invoice_refund.state, 'paid')

    def test_4_negative_supplier_invoice_payment(self):
        self.supplier_negative_invoice.action_invoice_open()
        self.assertEqual(self.supplier_negative_invoice.amount_total, -100.0)
        self.assertAlmostEquals(self.supplier_negative_invoice.residual, 100.0)
        ctx = {'active_model': 'account.invoice',
               'active_ids': [self.supplier_negative_invoice.id]}
        register_payments = \
            self.register_payments_model.with_context(ctx).create({
                'payment_date': fields.Date.to_string(date.today()),
                'journal_id': self.bank_journal.id,
                'payment_method_id': self.payment_method_check.id
            })
        register_payments.create_payment()
        payment = self.payment_model.search([], order="id desc", limit=1)
        self.assertAlmostEquals(payment.amount, 100)
        self.assertAlmostEquals(payment.payment_difference, -100)
        self.assertEqual(payment.state, 'posted')
        self.assertEqual(self.supplier_negative_invoice.state, 'paid')

        # rest refund negativeinvoice
        # I refund the invoice Using Refund Button
        invoice_refund_obj = self.env['account.invoice.refund']
        account_invoice_refund = invoice_refund_obj.create(dict(
            description='Refund invoice',
            date=fields.Date.to_string(date.today()),
            filter_refund='refund'
        ))

        # I clicked on refund button.
        account_invoice_refund.with_context({
            'active_ids': [self.supplier_negative_invoice.id]
        }).invoice_refund()
        invoice_refund = self.env['account.invoice'].search(
            [], order='id desc', limit=1)
        invoice_refund.action_invoice_open()
        self.assertEqual(invoice_refund.amount_total, -100.0)
        self.assertAlmostEquals(invoice_refund.residual, 100.0)
        self.assertEqual(invoice_refund.type, 'in_refund')
        ctx1 = {'active_model': 'account.invoice',
                'active_ids': [invoice_refund.id]}
        refund_register_payments = \
            self.register_payments_model.with_context(ctx1).create({
                'payment_date': fields.Date.to_string(date.today()),
                'journal_id': self.bank_journal.id,
                'payment_method_id': self.payment_method_check.id
            })
        refund_register_payments.create_payment()
        refund_payment = self.payment_model.search(
            [], order="id desc", limit=1)
        self.assertAlmostEquals(refund_payment.amount, 100)
        self.assertAlmostEquals(refund_payment.payment_difference, 100)
        self.assertEqual(refund_payment.state, 'posted')
        self.assertEqual(invoice_refund.state, 'paid')
