# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date

from dateutil.relativedelta import relativedelta

from odoo.exceptions import UserError
from odoo.tests.common import Form

from .common import TestAccountCashDiscountCommon


class TestAccountCashDiscountBase(TestAccountCashDiscountCommon):
    def create_simple_invoice(self, amount):
        invoice_date = date.today()
        invoice_form = Form(
            self.AccountMove.with_context(
                default_move_type="in_invoice",
                default_company_id=self.company.id,
                default_invoice_date=invoice_date,
            )
        )
        invoice_form.partner_id = self.partner_agrolait

        with invoice_form.invoice_line_ids.new() as line_form:
            line_form.name = "test"
            line_form.quantity = 1
            line_form.account_id = self.exp_account
            line_form.price_unit = amount
            line_form.tax_ids.clear()
            line_form.tax_ids.add(self.tax_10_p)

        invoice = invoice_form.save()
        return invoice

    def test_company_use_tax_adjustment(self):
        self.company.cash_discount_base_amount_type = "untaxed"
        self.assertFalse(self.company.cash_discount_use_tax_adjustment)

        self.company.cash_discount_base_amount_type = "total"
        self.assertTrue(self.company.cash_discount_use_tax_adjustment)

    def test_invoice_has_discount(self):
        invoice = self.create_simple_invoice(1000)
        self.assertFalse(invoice.has_discount)

        invoice.discount_percent = 10
        self.assertFalse(invoice.has_discount)

        invoice.discount_delay = 10
        invoice._onchange_discount_delay()
        self.assertTrue(invoice.has_discount)

    def test_compute_discount_untaxed(self):
        self.company.cash_discount_base_amount_type = "untaxed"
        invoice = self.create_simple_invoice(1000)

        invoice.discount_percent = 0
        self.assertEqual(invoice.discount_amount, 0)
        self.assertEqual(invoice.amount_total_with_discount, 1100)

        invoice.discount_percent = 10
        self.assertEqual(invoice.discount_amount, 100)
        self.assertEqual(invoice.amount_total_with_discount, 1000)

    def test_compute_discount_total(self):
        self.company.cash_discount_base_amount_type = "total"
        invoice = self.create_simple_invoice(1000)

        invoice.discount_percent = 0
        self.assertEqual(invoice.discount_amount, 0)
        self.assertEqual(invoice.amount_total_with_discount, 1100)

        invoice.discount_percent = 10
        self.assertEqual(invoice.discount_amount, 110)
        self.assertEqual(invoice.amount_total_with_discount, 990)

    def test_discount_delay_1(self):
        days_delay = 10
        today = date.today()
        today_10_days_later = today + relativedelta(days=days_delay)

        invoice = self.create_simple_invoice(100)
        invoice.discount_delay = days_delay
        invoice._onchange_discount_delay()
        self.assertFalse(invoice.discount_due_date)

        invoice.invalidate_cache()
        invoice.discount_percent = 10
        invoice._onchange_discount_delay()
        self.assertEqual(invoice.discount_due_date, today_10_days_later)

    def test_discount_delay_2(self):
        invoice = self.create_simple_invoice(100)
        invoice.discount_percent = 10

        with self.assertRaises(UserError) as e, self.env.cr.savepoint():
            invoice.action_post()

        self.assertTrue(
            "You can't set a discount amount if there is no " "discount due date",
            e.exception.args[0],
        )

        invoice.discount_delay = 10
        invoice._onchange_discount_delay()
        self.assertTrue(invoice.discount_due_date)
        invoice.action_post()

    def test_onchange_payment_term(self):
        payment_term = self.payment_term
        payment_term.discount_percent = 5
        payment_term.discount_delay = 5

        invoice = self.create_simple_invoice(100)
        self.assertEqual(invoice.discount_percent, payment_term.discount_percent)
        self.assertEqual(invoice.discount_delay, payment_term.discount_delay)
