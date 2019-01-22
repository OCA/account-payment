# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.account_cash_discount_payment.tests.common import \
    TestAccountCashDiscountPaymentCommon
from odoo.exceptions import UserError
from odoo.fields import Date


class TestAccountCashDiscountWriteOff(TestAccountCashDiscountPaymentCommon):

    @classmethod
    def setUpClass(cls):
        super(TestAccountCashDiscountWriteOff, cls).setUpClass()
        cls.cash_discount_writeoff_account = cls.Account.create({
            'name': "Cash Discount Write-Off",
            'code': "CD-W",
            'user_type_id': cls.inc_account_type.id,
        })

        cls.cash_discount_writeoff_journal = cls.Journal.create({
            'name': "Cash Discount Write-Off",
            'code': "CD-W",
            'type': 'general',
        })

    def test_cash_discount_with_write_off(self):
        payment_mode = self.payment_mode_out
        payment_mode.post_move = True
        discount_due_date = Date.today()

        invoice = self.create_supplier_invoice(
            discount_due_date, payment_mode, 1000, 10, [])
        invoice.action_invoice_open()

        move = invoice.move_id
        move.post()

        payment_order = self.PaymentOrder.create({
            'payment_mode_id': payment_mode.id,
            'payment_type': 'outbound',
            'journal_id': self.bank_ing_journal.id,
        })

        payment_line_wizard = self.PaymentLineCreate.with_context(
            active_model=payment_order._name,
            active_id=payment_order.id,
        ).create({
            'cash_discount_date': discount_due_date,
            'date_type': 'discount_due_date',
            'journal_ids': [(6, 0, [self.purchase_journal.id])],
        })

        payment_line_wizard.populate()
        payment_line_wizard.create_payment_lines()

        payment_order.draft2open()

        payment_line = payment_order.payment_line_ids[0]
        self.assertTrue(payment_line.pay_with_discount)
        self.assertTrue(payment_line._check_cash_discount_write_off_creation())
        old_amount = payment_line.amount_currency
        payment_line.amount_currency = 10
        self.assertFalse(
            payment_line._check_cash_discount_write_off_creation())
        payment_line.amount_currency = old_amount

        payment_order.open2generated()

        with self.assertRaises(UserError), self.env.cr.savepoint():
            payment_order.generated2uploaded()

        self.company.write({
            'default_cash_discount_writeoff_account_id':
                self.cash_discount_writeoff_account.id,
            'default_cash_discount_writeoff_journal_id':
                self.cash_discount_writeoff_journal.id,
        })

        payment_order.generated2uploaded()

        payment_move_lines = invoice.payment_move_line_ids
        write_off_line = self.MoveLine.search([
            ('id', 'in', payment_move_lines.ids),
            ('name', '=', "Cash Discount Write-Off"),
        ])

        self.assertEqual(len(write_off_line), 1)
        self.assertEqual(write_off_line.debit, 100)

        write_off_base_line = self.MoveLine.search([
            ('id', '!=', write_off_line.id),
            ('move_id', '=', write_off_line.move_id.id),
        ])
        self.assertEqual(len(write_off_base_line), 1)
        self.assertEqual(
            write_off_base_line.account_id,
            self.cash_discount_writeoff_account)
        self.assertEqual(invoice.state, 'paid')

    def test_cash_discount_with_write_off_with_taxes(self):
        self.company.write({
            'default_cash_discount_writeoff_account_id':
                self.cash_discount_writeoff_account.id,
            'default_cash_discount_writeoff_journal_id':
                self.cash_discount_writeoff_journal.id,
            'cash_discount_base_amount_type': 'total',
        })
        self.assertEqual(self.company.cash_discount_base_amount_type, 'total')

        payment_mode = self.payment_mode_out
        payment_mode.post_move = True
        discount_due_date = Date.today()

        invoice = self.create_supplier_invoice(
            discount_due_date, payment_mode, 1000, 10,
            [self.tax_10_p.id, self.tax_15_p.id])
        invoice.action_invoice_open()

        move = invoice.move_id
        move.post()

        payment_order = self.PaymentOrder.create({
            'payment_mode_id': payment_mode.id,
            'payment_type': 'outbound',
            'journal_id': self.bank_ing_journal.id,
        })

        payment_line_wizard = self.PaymentLineCreate.with_context(
            active_model=payment_order._name,
            active_id=payment_order.id,
        ).create({
            'cash_discount_date': discount_due_date,
            'date_type': 'discount_due_date',
            'journal_ids': [(6, 0, [self.purchase_journal.id])],
        })

        payment_line_wizard.populate()
        payment_line_wizard.create_payment_lines()

        payment_order.draft2open()
        payment_order.open2generated()
        payment_order.generated2uploaded()

        self.assertEqual(invoice.state, 'paid')

        discount_writeoff_move_lines = self.MoveLine.search([
            ('journal_id',
             '=', self.cash_discount_writeoff_journal.id)
        ])
        self.assertEqual(len(discount_writeoff_move_lines), 4)

        tax_10_move_line = self.MoveLine.search([
            ('id', 'in', discount_writeoff_move_lines.ids),
            ('tax_line_id', '=', self.tax_10_p.id),
        ])
        self.assertEqual(len(tax_10_move_line), 1)
        self.assertEqual(tax_10_move_line.credit, 10)

        tax_15_move_line = self.MoveLine.search([
            ('id', 'in', discount_writeoff_move_lines.ids),
            ('tax_line_id', '=', self.tax_15_p.id),
        ])
        self.assertEqual(len(tax_15_move_line), 1)
        self.assertEqual(tax_15_move_line.credit, 15)

    def test_cash_discount_with_refund(self):
        self.company.write({
            'default_cash_discount_writeoff_account_id':
                self.cash_discount_writeoff_account.id,
            'default_cash_discount_writeoff_journal_id':
                self.cash_discount_writeoff_journal.id,
            'cash_discount_base_amount_type': 'total',
        })

        payment_mode = self.payment_mode_out
        payment_mode.post_move = True
        discount_due_date = Date.today()

        invoice = self.create_supplier_invoice(
            discount_due_date, payment_mode, 100, 2,
            [self.tax_17_p.id])
        invoice.action_invoice_open()
        self.assertAlmostEqual(invoice.residual, 117)
        self.assertAlmostEqual(invoice.residual_with_discount, 114.66)

        move = invoice.move_id
        move.post()

        self.AccountInvoiceRefund.create({}).with_context(
            active_ids=invoice.ids,
        ).compute_refund()

        refund = self.AccountInvoice.search([
            ('origin', '=', invoice.number),
            ('type', '=', 'in_refund'),
        ])
        refund.invoice_line_ids[0].price_unit = 10
        refund.write({
            'discount_due_date': discount_due_date,
            'discount_percent': 2,
        })
        refund.compute_taxes()
        refund.action_invoice_open()
        credit_aml_id = self.AccountMoveLine.search([
            ('move_id', '=', refund.move_id.id),
            ('debit', '>', 0),
        ], limit=1)

        invoice.assign_outstanding_credit(credit_aml_id.id)

        self.assertAlmostEqual(invoice.residual, 105.3)
        self.assertAlmostEqual(invoice.residual_with_discount, 103.19)

        payment_order = self.PaymentOrder.create({
            'payment_mode_id': payment_mode.id,
            'payment_type': 'outbound',
            'journal_id': self.bank_ing_journal.id,
        })

        payment_line_wizard = self.PaymentLineCreate.with_context(
            active_model=payment_order._name,
            active_id=payment_order.id,
        ).create({
            'cash_discount_date': discount_due_date,
            'date_type': 'discount_due_date',
            'journal_ids': [(6, 0, [self.purchase_journal.id])],
        })

        payment_line_wizard.populate()
        payment_line_wizard.create_payment_lines()

        payment_line = payment_order.payment_line_ids[0]
        self.assertAlmostEqual(payment_line.amount_currency, 103.19)

        payment_order.draft2open()
        payment_order.open2generated()
        payment_order.generated2uploaded()

        self.assertEqual(invoice.state, 'paid')
