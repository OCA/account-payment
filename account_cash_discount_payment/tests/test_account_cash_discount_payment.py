# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.exceptions import ValidationError
from odoo.fields import Date

from .common import TestAccountCashDiscountPaymentCommon


class TestAccountCashDiscountPayment(TestAccountCashDiscountPaymentCommon):
    def create_payment_order(self, invoice_date, invoice):
        payment_order = self.PaymentOrder.create(
            {"payment_mode_id": self.payment_mode_out.id, "payment_type": "outbound"}
        )
        payment_line_wizard = self.PaymentLineCreate.with_context(
            active_model=payment_order._name,
            active_id=payment_order.id,
        ).create(
            {
                "cash_discount_date": invoice_date,
                "date_type": "discount_due_date",
                "target_move": "posted",
                "journal_ids": [(6, 0, [invoice.journal_id.id])],
            }
        )
        self.assertEqual(payment_line_wizard.order_id, payment_order)

        payment_line_wizard.populate()
        payment_line_wizard.create_payment_lines()

        return payment_order

    def test_invoice_payment_discount(self):
        invoice_date = Date.today()

        payment_term = self.env["account.payment.term"].create(
            {
                "name": "25% discount 0 days",
                "line_ids": [
                    Command.create(
                        {
                            "value": "balance",
                            "value_amount": 0.0,
                            "months": 0,
                            "end_month": False,
                            "discount_percentage": 25,
                            "discount_days": 5,
                        }
                    )
                ],
            }
        )

        invoice = self.create_supplier_invoice(
            invoice_date, self.payment_mode_out, 2000, False, payment_term
        )
        invoice._onchange_discount_delay()
        invoice.action_post()

        payment_order = self.PaymentOrder.create(
            {"payment_mode_id": self.payment_mode_out.id, "payment_type": "outbound"}
        )

        payment_line_wizard = self.PaymentLineCreate.with_context(
            active_model=payment_order._name,
            active_id=payment_order.id,
        ).create(
            {
                "cash_discount_date": invoice_date,
                "date_type": "discount_due_date",
                "target_move": "posted",
                "journal_ids": [(6, 0, [invoice.journal_id.id])],
            }
        )
        self.assertEqual(payment_line_wizard.order_id, payment_order)

        payment_line_wizard.populate()
        move_lines = payment_line_wizard.move_line_ids
        self.assertEqual(len(move_lines), 1)

        move_line = move_lines[0]
        self.assertAlmostEqual(move_line.discount_amount, 500, 2)

        payment_line_wizard.create_payment_lines()

        self.assertEqual(len(payment_order.payment_line_ids), 1)
        payment_line = payment_order.payment_line_ids[0]
        self.assertTrue(payment_line.pay_with_discount)
        self.assertAlmostEqual(payment_line.amount_currency, 1500)

        # Change the amount of the line and trigger the onchange amount method
        # and verify there is a warning
        payment_line.amount_currency = 125
        onchange_res = payment_line._onchange_amount_with_discount()
        self.assertTrue("warning" in onchange_res)
        self.assertFalse(payment_line.pay_with_discount)

        # Change it back to use the discount
        payment_line.pay_with_discount = True
        payment_line._onchange_pay_with_discount()
        self.assertAlmostEqual(payment_line.amount_currency, 1500)

        # Check pay_with_discount_constraint
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            payment_line.move_line_id = False

        # Change pay_with_discount and check if discount amount is coherent
        # with the invoice
        payment_line.pay_with_discount = False
        payment_line._onchange_pay_with_discount()
        self.assertEqual(payment_line.amount_currency, invoice.amount_total)

        payment_line.pay_with_discount = True
        payment_line._onchange_pay_with_discount()
        self.assertEqual(
            payment_line.amount_currency, invoice.amount_total - invoice.discount_amount
        )

        self.assertAlmostEqual(payment_line.discount_amount, 500, 2)
        self.assertAlmostEqual(payment_line.amount_currency, 1500, 2)

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
        invoice_date = Date.today()
        self.env.company.cash_discount_base_amount_type = "total"
        invoice = self.create_supplier_invoice(
            invoice_date,
            self.payment_mode_out,
            1500,
            self.tax_20_p,
            self.payment_term_2_p_discount_7d,
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
        invoice.action_post()

        payment_order = self.create_payment_order(invoice_date, invoice)

        self.assertEqual(len(payment_order.payment_line_ids), 1)
        payment_line = payment_order.payment_line_ids[0]
        self.assertTrue(payment_line.pay_with_discount)
        self.assertAlmostEqual(payment_line.amount_currency, 1764.0)
        self.assertTrue(payment_line.pay_with_discount)

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
        invoice_date = Date.today()
        self.env.company.cash_discount_base_amount_type = "untaxed"
        invoice = self.create_supplier_invoice(
            invoice_date,
            self.payment_mode_out,
            1500,
            self.tax_20_p,
            self.payment_term_2_p_discount_7d,
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

        invoice.action_post()

        payment_order = self.create_payment_order(invoice_date, invoice)

        self.assertEqual(len(payment_order.payment_line_ids), 1)
        payment_line = payment_order.payment_line_ids[0]
        self.assertTrue(payment_line.pay_with_discount)
        self.assertAlmostEqual(payment_line.amount_currency, 1770.0)
        self.assertTrue(payment_line.pay_with_discount)

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
        invoice_date = Date.today()
        self.env.company.cash_discount_base_amount_type = "total"
        invoice = self.create_supplier_invoice(
            invoice_date,
            self.payment_mode_out,
            1500,
            self.tax_20_p,
            self.payment_term_2_p_discount_7d,
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

        payment_order = self.create_payment_order(invoice_date, invoice)

        self.assertEqual(len(payment_order.payment_line_ids), 1)
        payment_line = payment_order.payment_line_ids[0]
        self.assertTrue(payment_line.pay_with_discount)
        self.assertAlmostEqual(payment_line.amount_currency, 1176.0)
        self.assertTrue(payment_line.pay_with_discount)

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
        invoice_date = Date.today()
        self.env.company.cash_discount_base_amount_type = "untaxed"
        invoice = self.create_supplier_invoice(
            invoice_date,
            self.payment_mode_out,
            1500,
            self.tax_20_p,
            self.payment_term_2_p_discount_7d,
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

        payment_order = self.create_payment_order(invoice_date, invoice)

        self.assertEqual(len(payment_order.payment_line_ids), 1)
        payment_line = payment_order.payment_line_ids[0]
        self.assertTrue(payment_line.pay_with_discount)
        self.assertAlmostEqual(payment_line.amount_currency, 1180.0)
        self.assertTrue(payment_line.pay_with_discount)

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
        invoice_date = Date.today()
        self.env.company.cash_discount_base_amount_type = "total"
        invoice = self.create_supplier_invoice(
            invoice_date,
            self.payment_mode_out,
            1500,
            self.tax_20_p,
            self.payment_term_2_p_discount_7d,
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

        payment_order = self.create_payment_order(invoice_date, invoice)

        self.assertEqual(len(payment_order.payment_line_ids), 1)
        payment_line = payment_order.payment_line_ids[0]
        self.assertTrue(payment_line.pay_with_discount)
        self.assertAlmostEqual(payment_line.amount_currency, 940.8)
        self.assertTrue(payment_line.pay_with_discount)

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
        invoice_date = Date.today()
        self.env.company.cash_discount_base_amount_type = "untaxed"
        invoice = self.create_supplier_invoice(
            invoice_date,
            self.payment_mode_out,
            1500,
            self.tax_20_p,
            self.payment_term_2_p_discount_7d,
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
                    "real_discount_amount": 16.0,
                    "refunds_discount_amount": 14.0,
                    "residual_with_discount": 944.0,
                    "invoice_payment_term_id": self.payment_term_2_p_discount_7d.id,
                }
            ],
        )

        payment_order = self.create_payment_order(invoice_date, invoice)

        self.assertEqual(len(payment_order.payment_line_ids), 1)
        payment_line = payment_order.payment_line_ids[0]
        self.assertTrue(payment_line.pay_with_discount)
        self.assertAlmostEqual(payment_line.amount_currency, 944.0)
        self.assertTrue(payment_line.pay_with_discount)
