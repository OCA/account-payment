# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests.common import Form

from .common import TestAccountCashDiscountCommon


class TestAccountCashDiscountBase(TestAccountCashDiscountCommon):
    def create_simple_invoice(self, amount, tax=None, payment_term=None):
        invoice_date = date.today()
        invoice_form = Form(
            self.AccountMove.with_context(
                default_move_type="in_invoice",
                default_company_id=self.company.id,
                default_invoice_date=invoice_date,
            )
        )
        invoice_form.partner_id = self.partner_agrolait
        if payment_term:
            invoice_form.invoice_payment_term_id = payment_term

        with invoice_form.invoice_line_ids.new() as line_form:
            line_form.name = "test"
            line_form.quantity = 1
            line_form.price_unit = amount
            line_form.tax_ids.clear()
            tax_id = tax or self.tax_10_p
            line_form.tax_ids.add(tax_id)

        invoice = invoice_form.save()
        # account_id not present in form
        invoice.invoice_line_ids.account_id = self.exp_account.id
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

        invoice.invalidate_model()
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

    def test_invoice_with_discount_1(self):
        """
        Discount: Tax included
        Invoice:
            Amount without Tax: 1500
            Tax: 20% (300)
            Total on invoice: 1800
            Discount: 2% (36)
            Total with discount: 1764
        """
        self.env.company.cash_discount_base_amount_type = "total"
        invoice = self.create_simple_invoice(
            1500, self.tax_20_p, self.payment_term_2_p_discount_7d
        )
        invoice._onchange_discount_delay()
        self.assertTrue(invoice.has_discount)
        self.assertRecordValues(
            invoice,
            [
                {
                    "amount_untaxed": 1500.0,
                    "amount_tax": 300.0,
                    "amount_total": 1800.0,
                    "discount_amount": 36.0,
                    "discount_percent": 2.0,
                    "amount_total_with_discount": 1764.0,
                }
            ],
        )

    def test_invoice_with_discount_2(self):
        """
        Discount: Tax excluded
        Invoice:
            Amount without Tax: 1500
            Tax: 20% (300)
            Total on invoice: 1800
            Discount: 2% (30)
            Total with discount: 1770
        """
        self.env.company.cash_discount_base_amount_type = "untaxed"
        invoice = self.create_simple_invoice(
            1500, self.tax_20_p, self.payment_term_2_p_discount_7d
        )
        invoice._onchange_discount_delay()
        self.assertTrue(invoice.has_discount)
        self.assertRecordValues(
            invoice,
            [
                {
                    "amount_untaxed": 1500.0,
                    "amount_tax": 300.0,
                    "amount_total": 1800.0,
                    "discount_amount": 30.0,
                    "discount_percent": 2.0,
                    "amount_total_with_discount": 1770.0,
                }
            ],
        )

    def test_invoice_with_discount_with_cn_1(self):
        """
        Discount: Tax included
        Invoice:
            Amount without Tax: 1500
            Tax: 20% (300)
            Total on invoice: 1800
            Discount: 2% (36)

        Credit Note:
            Amount without Tax: 500
            Tax: 20% (100)
            Total on invoice: 600
            Discount: 2% (12)

            Total with discount: 1176
        """
        self.env.company.cash_discount_base_amount_type = "total"

        invoice = self.create_simple_invoice(
            1500, self.tax_20_p, self.payment_term_2_p_discount_7d
        )
        invoice._onchange_discount_delay()
        self.assertTrue(invoice.has_discount)
        self.assertRecordValues(
            invoice,
            [
                {
                    "amount_untaxed": 1500.0,
                    "amount_tax": 300.0,
                    "amount_total": 1800.0,
                    "discount_amount": 36.0,
                    "discount_percent": 2.0,
                    "amount_total_with_discount": 1764.0,
                    "real_discount_amount": 36.0,
                    "refunds_discount_amount": 0.0,
                    "residual_with_discount": 1764.0,
                    "invoice_payment_term_id": self.payment_term_2_p_discount_7d.id,
                }
            ],
        )
        invoice.action_post()

        move_reversal = (
            self.env["account.move.reversal"]
            .with_context(active_model="account.move", active_ids=invoice.ids)
            .create(
                {
                    "refund_method": "refund",
                    "journal_id": invoice.journal_id.id,
                }
            )
        )
        reversal = move_reversal.reverse_moves()
        reversed_move = self.env["account.move"].browse(reversal["res_id"])
        reversed_move.write(
            {
                "invoice_line_ids": [
                    Command.update(
                        reversed_move.invoice_line_ids.id, {"price_unit": 500}
                    ),
                ],
            }
        )
        reversed_move.action_post()
        self.assertRecordValues(
            reversed_move,
            [
                {
                    "amount_untaxed": 500.0,
                    "amount_tax": 100.0,
                    "amount_total": 600.0,
                    "discount_amount": 12.0,
                    "discount_percent": 2.0,
                    "amount_total_with_discount": 588.0,
                    "invoice_payment_term_id": self.payment_term_2_p_discount_7d.id,
                }
            ],
        )

        (invoice + reversed_move).line_ids.filtered(
            lambda line: line.account_type in ("asset_receivable", "liability_payable")
        ).reconcile()

        self.assertRecordValues(
            invoice,
            [
                {
                    "amount_untaxed": 1500.0,
                    "amount_tax": 300.0,
                    "amount_total": 1800.0,
                    "discount_amount": 36.0,
                    "discount_percent": 2.0,
                    "amount_total_with_discount": 1764.0,
                    "real_discount_amount": 24.0,
                    "refunds_discount_amount": 12.0,
                    "residual_with_discount": 1176.0,
                    "invoice_payment_term_id": self.payment_term_2_p_discount_7d.id,
                }
            ],
        )

    def test_invoice_with_discount_with_cn_2(self):
        """
        Discount: Tax excluded
        Invoice:
            Amount without Tax: 1500
            Tax: 20% (300)
            Total on invoice: 1800
            Discount: 2% (20)

        Credit Note:
            Amount without Tax: 500
            Tax: 20% (100)
            Total on invoice: 600
            Discount: 2% (10)

            Total with discount: 1180
        """
        self.env.company.cash_discount_base_amount_type = "untaxed"

        invoice = self.create_simple_invoice(
            1500, self.tax_20_p, self.payment_term_2_p_discount_7d
        )
        invoice._onchange_discount_delay()
        self.assertTrue(invoice.has_discount)
        self.assertRecordValues(
            invoice,
            [
                {
                    "amount_untaxed": 1500.0,
                    "amount_tax": 300.0,
                    "amount_total": 1800.0,
                    "discount_amount": 30.0,
                    "discount_percent": 2.0,
                    "amount_total_with_discount": 1770.0,
                    "real_discount_amount": 30.0,
                    "refunds_discount_amount": 0.0,
                    "residual_with_discount": 1770.0,
                    "invoice_payment_term_id": self.payment_term_2_p_discount_7d.id,
                }
            ],
        )
        invoice.action_post()

        move_reversal = (
            self.env["account.move.reversal"]
            .with_context(active_model="account.move", active_ids=invoice.ids)
            .create(
                {
                    "refund_method": "refund",
                    "journal_id": invoice.journal_id.id,
                }
            )
        )
        reversal = move_reversal.reverse_moves()
        reversed_move = self.env["account.move"].browse(reversal["res_id"])
        reversed_move.write(
            {
                "invoice_line_ids": [
                    Command.update(
                        reversed_move.invoice_line_ids.id, {"price_unit": 500}
                    ),
                ],
            }
        )
        reversed_move.action_post()
        self.assertRecordValues(
            reversed_move,
            [
                {
                    "amount_untaxed": 500.0,
                    "amount_tax": 100.0,
                    "amount_total": 600.0,
                    "discount_amount": 10.0,
                    "discount_percent": 2.0,
                    "amount_total_with_discount": 590.0,
                    "invoice_payment_term_id": self.payment_term_2_p_discount_7d.id,
                }
            ],
        )

        (invoice + reversed_move).line_ids.filtered(
            lambda line: line.account_type in ("asset_receivable", "liability_payable")
        ).reconcile()

        self.assertRecordValues(
            invoice,
            [
                {
                    "amount_untaxed": 1500.0,
                    "amount_tax": 300.0,
                    "amount_total": 1800.0,
                    "discount_amount": 30.0,
                    "discount_percent": 2.0,
                    "amount_total_with_discount": 1770.0,
                    "real_discount_amount": 20.0,
                    "refunds_discount_amount": 10.0,
                    "residual_with_discount": 1180.0,
                    "invoice_payment_term_id": self.payment_term_2_p_discount_7d.id,
                }
            ],
        )

    def test_invoice_with_discount_with_cn_3(self):
        """
        Discount: Tax included
        Invoice:
            Amount without Tax: 1500
            Tax: 20% (300)
            Total on invoice: 1800
            Discount: 2% (36)

        Credit Note:
            Amount without Tax: 500
            Tax: 20% (100)
            Total on invoice: 600
            Discount: 2% (12)

        Credit Note:
            Amount without Tax: 200
            Tax: 20% (40)
            Total on invoice: 240
            Discount: 2% (4.8)

            Total with discount: 940.8
        """
        self.env.company.cash_discount_base_amount_type = "total"

        invoice = self.create_simple_invoice(
            1500, self.tax_20_p, self.payment_term_2_p_discount_7d
        )
        invoice._onchange_discount_delay()
        self.assertTrue(invoice.has_discount)
        self.assertRecordValues(
            invoice,
            [
                {
                    "amount_untaxed": 1500.0,
                    "amount_tax": 300.0,
                    "amount_total": 1800.0,
                    "discount_amount": 36.0,
                    "discount_percent": 2.0,
                    "amount_total_with_discount": 1764.0,
                    "real_discount_amount": 36.0,
                    "refunds_discount_amount": 0.0,
                    "residual_with_discount": 1764.0,
                    "invoice_payment_term_id": self.payment_term_2_p_discount_7d.id,
                }
            ],
        )
        invoice.action_post()

        move_reversal = (
            self.env["account.move.reversal"]
            .with_context(active_model="account.move", active_ids=invoice.ids)
            .create(
                {
                    "refund_method": "refund",
                    "journal_id": invoice.journal_id.id,
                }
            )
        )
        reversal = move_reversal.reverse_moves()
        reversed_move = self.env["account.move"].browse(reversal["res_id"])
        reversed_move.write(
            {
                "invoice_line_ids": [
                    Command.update(
                        reversed_move.invoice_line_ids.id, {"price_unit": 500}
                    ),
                ],
            }
        )
        reversed_move.action_post()
        self.assertRecordValues(
            reversed_move,
            [
                {
                    "amount_untaxed": 500.0,
                    "amount_tax": 100.0,
                    "amount_total": 600.0,
                    "discount_amount": 12.0,
                    "discount_percent": 2.0,
                    "amount_total_with_discount": 588.0,
                    "invoice_payment_term_id": self.payment_term_2_p_discount_7d.id,
                }
            ],
        )

        (invoice + reversed_move).line_ids.filtered(
            lambda line: line.account_type in ("asset_receivable", "liability_payable")
        ).reconcile()

        self.assertRecordValues(
            invoice,
            [
                {
                    "amount_untaxed": 1500.0,
                    "amount_tax": 300.0,
                    "amount_total": 1800.0,
                    "discount_amount": 36.0,
                    "discount_percent": 2.0,
                    "amount_total_with_discount": 1764.0,
                    "real_discount_amount": 24.0,
                    "refunds_discount_amount": 12.0,
                    "residual_with_discount": 1176.0,
                    "invoice_payment_term_id": self.payment_term_2_p_discount_7d.id,
                }
            ],
        )

        move_reversal2 = (
            self.env["account.move.reversal"]
            .with_context(active_model="account.move", active_ids=invoice.ids)
            .create(
                {
                    "refund_method": "refund",
                    "journal_id": invoice.journal_id.id,
                }
            )
        )
        reversal2 = move_reversal2.reverse_moves()
        reversed_move2 = self.env["account.move"].browse(reversal2["res_id"])
        reversed_move2.write(
            {
                "ref": "Second refund",
                "invoice_line_ids": [
                    Command.update(
                        reversed_move2.invoice_line_ids.id, {"price_unit": 200}
                    ),
                ],
            }
        )
        reversed_move2.action_post()

        self.assertRecordValues(
            reversed_move2,
            [
                {
                    "amount_untaxed": 200.0,
                    "amount_tax": 40.0,
                    "amount_total": 240.0,
                    "discount_amount": 4.8,
                    "discount_percent": 2.0,
                    "amount_total_with_discount": 235.2,
                    "invoice_payment_term_id": self.payment_term_2_p_discount_7d.id,
                }
            ],
        )

        (invoice + reversed_move2).line_ids.filtered(
            lambda line: line.account_type in ("asset_receivable", "liability_payable")
        ).reconcile()

        self.assertRecordValues(
            invoice,
            [
                {
                    "amount_untaxed": 1500.0,
                    "amount_tax": 300.0,
                    "amount_total": 1800.0,
                    "discount_amount": 36.0,
                    "discount_percent": 2.0,
                    "amount_total_with_discount": 1764.0,
                    "real_discount_amount": 19.2,
                    "refunds_discount_amount": 16.8,
                    "residual_with_discount": 940.8,
                    "invoice_payment_term_id": self.payment_term_2_p_discount_7d.id,
                }
            ],
        )

    def test_invoice_with_discount_with_cn_4(self):
        """
        Discount: Tax excluded
        Invoice:
            Amount without Tax: 1500
            Tax: 20% (300)
            Total on invoice: 1800
            Discount: 2% (30)

        Credit Note:
            Amount without Tax: 500
            Tax: 20% (100)
            Total on invoice: 600
            Discount: 2% (10)

        Credit Note:
            Amount without Tax: 200
            Tax: 20% (40)
            Total on invoice: 240
            Discount: 2% (4)

            Total with discount: 944
        """
        self.env.company.cash_discount_base_amount_type = "untaxed"

        invoice = self.create_simple_invoice(
            1500, self.tax_20_p, self.payment_term_2_p_discount_7d
        )
        invoice._onchange_discount_delay()
        self.assertTrue(invoice.has_discount)
        self.assertRecordValues(
            invoice,
            [
                {
                    "amount_untaxed": 1500.0,
                    "amount_tax": 300.0,
                    "amount_total": 1800.0,
                    "discount_amount": 30.0,
                    "discount_percent": 2.0,
                    "amount_total_with_discount": 1770.0,
                    "real_discount_amount": 30.0,
                    "refunds_discount_amount": 0.0,
                    "residual_with_discount": 1770.0,
                    "invoice_payment_term_id": self.payment_term_2_p_discount_7d.id,
                }
            ],
        )
        invoice.action_post()

        move_reversal = (
            self.env["account.move.reversal"]
            .with_context(active_model="account.move", active_ids=invoice.ids)
            .create(
                {
                    "refund_method": "refund",
                    "journal_id": invoice.journal_id.id,
                }
            )
        )
        reversal = move_reversal.reverse_moves()
        reversed_move = self.env["account.move"].browse(reversal["res_id"])
        reversed_move.write(
            {
                "invoice_line_ids": [
                    Command.update(
                        reversed_move.invoice_line_ids.id, {"price_unit": 500}
                    ),
                ],
            }
        )
        reversed_move.action_post()
        self.assertRecordValues(
            reversed_move,
            [
                {
                    "amount_untaxed": 500.0,
                    "amount_tax": 100.0,
                    "amount_total": 600.0,
                    "discount_amount": 10.0,
                    "discount_percent": 2.0,
                    "amount_total_with_discount": 590.0,
                    "invoice_payment_term_id": self.payment_term_2_p_discount_7d.id,
                }
            ],
        )

        (invoice + reversed_move).line_ids.filtered(
            lambda line: line.account_type in ("asset_receivable", "liability_payable")
        ).reconcile()

        self.assertRecordValues(
            invoice,
            [
                {
                    "amount_untaxed": 1500.0,
                    "amount_tax": 300.0,
                    "amount_total": 1800.0,
                    "discount_amount": 30.0,
                    "discount_percent": 2.0,
                    "amount_total_with_discount": 1770.0,
                    "real_discount_amount": 20.0,
                    "refunds_discount_amount": 10.0,
                    "residual_with_discount": 1180.0,
                    "invoice_payment_term_id": self.payment_term_2_p_discount_7d.id,
                }
            ],
        )

        move_reversal2 = (
            self.env["account.move.reversal"]
            .with_context(active_model="account.move", active_ids=invoice.ids)
            .create(
                {
                    "refund_method": "refund",
                    "journal_id": invoice.journal_id.id,
                }
            )
        )
        reversal2 = move_reversal2.reverse_moves()
        reversed_move2 = self.env["account.move"].browse(reversal2["res_id"])
        reversed_move2.write(
            {
                "ref": "Second refund",
                "invoice_line_ids": [
                    Command.update(
                        reversed_move2.invoice_line_ids.id, {"price_unit": 200}
                    ),
                ],
            }
        )
        reversed_move2.action_post()

        self.assertRecordValues(
            reversed_move2,
            [
                {
                    "amount_untaxed": 200.0,
                    "amount_tax": 40.0,
                    "amount_total": 240.0,
                    "discount_amount": 4,
                    "discount_percent": 2.0,
                    "amount_total_with_discount": 236,
                    "invoice_payment_term_id": self.payment_term_2_p_discount_7d.id,
                }
            ],
        )

        (invoice + reversed_move2).line_ids.filtered(
            lambda line: line.account_type in ("asset_receivable", "liability_payable")
        ).reconcile()

        self.assertRecordValues(
            invoice,
            [
                {
                    "amount_untaxed": 1500.0,
                    "amount_tax": 300.0,
                    "amount_total": 1800.0,
                    "discount_amount": 30.0,
                    "discount_percent": 2.0,
                    "amount_total_with_discount": 1770.0,
                    "real_discount_amount": 16,
                    "refunds_discount_amount": 14,
                    "residual_with_discount": 944,
                    "invoice_payment_term_id": self.payment_term_2_p_discount_7d.id,
                }
            ],
        )
