# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.exceptions import UserError
from odoo.fields import Date
from odoo.tests.common import Form

from odoo.addons.account_cash_discount_payment.tests.common import (
    TestAccountCashDiscountPaymentCommon,
)


class TestAccountCashDiscountWriteOff(TestAccountCashDiscountPaymentCommon):
    def create_payment_order(self, invoice_date, invoice):
        payment_order = self.PaymentOrder.create(
            {
                "payment_mode_id": self.payment_mode_out.id,
                "payment_type": "outbound",
                "journal_id": self.bank_ing_journal.id,
            }
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

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cash_discount_writeoff_account = cls.Account.create(
            {
                "name": "Cash Discount Write-Off",
                "code": "CDW",
                "account_type": "income_other",
            }
        )

        cls.cash_discount_writeoff_journal = cls.Journal.create(
            {"name": "Cash Discount Write-Off", "code": "CD-W", "type": "general"}
        )

    def test_cash_discount_with_write_off(self):
        payment_mode = self.payment_mode_out
        payment_mode.post_move = True
        invoice_date = Date.today()

        payment_term = self.env["account.payment.term"].create(
            {
                "name": "10% discount 5 days",
                "line_ids": [
                    Command.create(
                        {
                            "value": "balance",
                            "value_amount": 0.0,
                            "months": 0,
                            "end_month": False,
                            "discount_percentage": 10,
                            "discount_days": 5,
                        }
                    )
                ],
            }
        )

        invoice = self.create_supplier_invoice(
            invoice_date, self.payment_mode_out, 1000, False, payment_term
        )
        invoice._onchange_discount_delay()
        invoice.ref = "test ref"
        invoice.action_post()

        payment_order = self.PaymentOrder.create(
            {
                "payment_mode_id": payment_mode.id,
                "payment_type": "outbound",
                "journal_id": self.bank_ing_journal.id,
            }
        )

        payment_line_wizard = self.PaymentLineCreate.with_context(
            active_model=payment_order._name,
            active_id=payment_order.id,
        ).create(
            {
                "cash_discount_date": invoice_date,
                "date_type": "discount_due_date",
                "journal_ids": [(6, 0, [invoice.journal_id.id])],
            }
        )

        payment_line_wizard.populate()
        payment_line_wizard.create_payment_lines()

        payment_order.draft2open()

        payment_line = payment_order.payment_line_ids[0]
        self.assertTrue(payment_line.pay_with_discount)
        self.assertTrue(payment_line._check_cash_discount_write_off_creation())
        old_amount = payment_line.amount_currency
        payment_line.amount_currency = 10
        self.assertFalse(payment_line._check_cash_discount_write_off_creation())
        payment_line.amount_currency = old_amount

        payment_order.open2generated()

        with self.assertRaises(UserError), self.env.cr.savepoint():
            payment_order.generated2uploaded()

        woff_account = self.cash_discount_writeoff_account
        woff_journal = self.cash_discount_writeoff_journal
        self.company.write(
            {
                "default_cash_discount_writeoff_account_id": woff_account.id,
                "default_cash_discount_writeoff_journal_id": woff_journal.id,
                "cash_discount_base_amount_type": "total",
            }
        )

        payment_order.generated2uploaded()

        payment_move_lines = invoice._get_payment_move_lines()
        write_off_line = self.MoveLine.search(
            [
                ("id", "in", payment_move_lines.ids),
                ("name", "=", "Cash Discount Write-Off"),
            ]
        )

        self.assertEqual(len(write_off_line), 1)
        self.assertEqual(write_off_line.debit, 100)

        write_off_base_line = self.MoveLine.search(
            [
                ("id", "!=", write_off_line.id),
                ("move_id", "=", write_off_line.move_id.id),
            ]
        )
        self.assertEqual(len(write_off_base_line), 1)
        self.assertEqual(
            write_off_base_line.account_id, self.cash_discount_writeoff_account
        )
        self.assertEqual(invoice.payment_state, "paid")

    def test_cash_discount_with_write_off_with_taxes(self):
        woff_account = self.cash_discount_writeoff_account
        woff_journal = self.cash_discount_writeoff_journal
        self.company.write(
            {
                "default_cash_discount_writeoff_account_id": woff_account.id,
                "default_cash_discount_writeoff_journal_id": woff_journal.id,
                "cash_discount_base_amount_type": "total",
            }
        )

        self.assertEqual(self.company.cash_discount_base_amount_type, "total")

        payment_mode = self.payment_mode_out
        payment_mode.post_move = True
        invoice_date = Date.today()

        payment_term = self.env["account.payment.term"].create(
            {
                "name": "10% discount 5 days",
                "line_ids": [
                    Command.create(
                        {
                            "value": "balance",
                            "value_amount": 0.0,
                            "months": 0,
                            "end_month": False,
                            "discount_percentage": 10,
                            "discount_days": 5,
                        }
                    )
                ],
            }
        )

        invoice = self.create_supplier_invoice(
            invoice_date, self.payment_mode_out, 1000, self.tax_10_p, payment_term
        )

        # add one tax
        inv_form = Form(
            invoice.with_context(
                default_move_type="in_invoice",
                default_company_id=self.company.id,
                default_payment_mode_id=payment_mode.id,
            )
        )
        with inv_form.invoice_line_ids.edit(0) as line:
            line.tax_ids.add(self.tax_15_p)

        invoice = inv_form.save()

        invoice._onchange_discount_delay()
        invoice.ref = "test ref"
        invoice.action_post()

        payment_order = self.PaymentOrder.create(
            {
                "payment_mode_id": payment_mode.id,
                "payment_type": "outbound",
                "journal_id": self.bank_ing_journal.id,
            }
        )

        payment_line_wizard = self.PaymentLineCreate.with_context(
            active_model=payment_order._name,
            active_id=payment_order.id,
        ).create(
            {
                "cash_discount_date": invoice_date,
                "date_type": "discount_due_date",
                "journal_ids": [(6, 0, [invoice.journal_id.id])],
            }
        )

        payment_line_wizard.populate()
        payment_line_wizard.create_payment_lines()

        payment_order.draft2open()
        payment_order.open2generated()
        payment_order.generated2uploaded()

        self.assertEqual(invoice.payment_state, "paid")

        discount_writeoff_move_lines = self.MoveLine.search(
            [("journal_id", "=", self.cash_discount_writeoff_journal.id)]
        )
        self.assertEqual(len(discount_writeoff_move_lines), 4)

        tax_10_move_line = self.MoveLine.search(
            [
                ("id", "in", discount_writeoff_move_lines.ids),
                ("tax_line_id", "=", self.tax_10_p.id),
            ]
        )
        self.assertEqual(len(tax_10_move_line), 1)
        self.assertEqual(tax_10_move_line.credit, 10)

        tax_15_move_line = self.MoveLine.search(
            [
                ("id", "in", discount_writeoff_move_lines.ids),
                ("tax_line_id", "=", self.tax_15_p.id),
            ]
        )
        self.assertEqual(len(tax_15_move_line), 1)
        self.assertEqual(tax_15_move_line.credit, 15)

    def test_cash_discount_with_refund(self):
        woff_account = self.cash_discount_writeoff_account
        woff_journal = self.cash_discount_writeoff_journal
        self.company.write(
            {
                "default_cash_discount_writeoff_account_id": woff_account.id,
                "default_cash_discount_writeoff_journal_id": woff_journal.id,
                "cash_discount_base_amount_type": "total",
            }
        )

        payment_mode = self.payment_mode_out
        payment_mode.post_move = True
        invoice_date = Date.today()

        payment_term = self.env["account.payment.term"].create(
            {
                "name": "2% discount 5 days",
                "line_ids": [
                    Command.create(
                        {
                            "value": "balance",
                            "value_amount": 0.0,
                            "months": 0,
                            "end_month": False,
                            "discount_percentage": 2,
                            "discount_days": 5,
                        }
                    )
                ],
            }
        )

        invoice = self.create_supplier_invoice(
            invoice_date, self.payment_mode_out, 100, self.tax_17_p, payment_term
        )
        invoice._onchange_discount_delay()
        invoice.ref = "test ref"
        invoice.action_post()
        self.assertAlmostEqual(invoice.amount_residual, 117)
        self.assertAlmostEqual(invoice.residual_with_discount, 114.66)

        move_reversal = self.AccountMoveReversal.with_context(
            active_model=invoice._name, active_ids=invoice.ids
        ).create(
            {
                "reason": "no reason",
                "refund_method": "refund",
                "journal_id": invoice.journal_id.id,
            }
        )
        reversal = move_reversal.reverse_moves()

        refund = self.env["account.move"].browse(reversal["res_id"])

        refund_form = Form(refund)
        with refund_form.invoice_line_ids.edit(0) as refund_line:
            refund_line.price_unit = 10
        refund_form.save()

        refund.write({"discount_due_date": invoice_date, "discount_percent": 2})
        refund.action_post()
        credit_aml_id = self.AccountMoveLine.search(
            [("move_id", "=", refund.id), ("debit", ">", 0)], limit=1
        )

        invoice.js_assign_outstanding_line(credit_aml_id.id)

        self.assertAlmostEqual(invoice.amount_residual, 105.3)
        self.assertAlmostEqual(invoice.residual_with_discount, 103.19)

        payment_order = self.PaymentOrder.create(
            {
                "payment_mode_id": payment_mode.id,
                "payment_type": "outbound",
                "journal_id": self.bank_ing_journal.id,
            }
        )

        payment_line_wizard = self.PaymentLineCreate.with_context(
            active_model=payment_order._name,
            active_id=payment_order.id,
        ).create(
            {
                "cash_discount_date": invoice_date,
                "date_type": "discount_due_date",
                "journal_ids": [(6, 0, [invoice.journal_id.id])],
            }
        )

        payment_line_wizard.populate()
        payment_line_wizard.create_payment_lines()

        payment_line = payment_order.payment_line_ids[0]
        self.assertAlmostEqual(payment_line.amount_currency, 103.19)

        payment_order.draft2open()
        payment_order.open2generated()
        payment_order.generated2uploaded()

        self.assertEqual(invoice.payment_state, "paid")

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
        woff_account = self.cash_discount_writeoff_account
        woff_journal = self.cash_discount_writeoff_journal
        payment_mode = self.payment_mode_out
        payment_mode.post_move = True
        self.company.write(
            {
                "default_cash_discount_writeoff_account_id": woff_account.id,
                "default_cash_discount_writeoff_journal_id": woff_journal.id,
                "cash_discount_base_amount_type": "total",
            }
        )
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
        invoice.ref = "test ref"
        invoice.action_post()

        payment_order = self.create_payment_order(invoice_date, invoice)

        self.assertEqual(len(payment_order.payment_line_ids), 1)
        payment_line = payment_order.payment_line_ids[0]
        self.assertTrue(payment_line.pay_with_discount)
        self.assertAlmostEqual(payment_line.amount_currency, 1764.0)
        self.assertTrue(payment_line.pay_with_discount)

        payment_order.draft2open()
        payment_order.open2generated()
        payment_order.generated2uploaded()

        self.assertEqual(len(payment_order.move_ids), 1)

        self.assertEqual(invoice.payment_state, "paid")

        domain_reconlied_line = payment_order.move_ids.open_reconcile_view()["domain"]
        reconciled_line_ids = self.env["account.move.line"].search(
            domain_reconlied_line
        )

        self.assertRecordValues(
            reconciled_line_ids.sorted(lambda r: r.balance),
            [
                {
                    "balance": -1800.0,
                },
                {
                    "balance": 36.0,
                    "name": "Cash Discount Write-Off",
                },
                {
                    "balance": 1764.0,
                    "name": "test ref",
                },
            ],
        )

        write_off_move = reconciled_line_ids.filtered(
            lambda r: r.journal_id == woff_journal
        ).move_id

        self.assertRecordValues(
            write_off_move.line_ids.sorted(lambda r: r.balance),
            [
                {
                    "balance": -30.0,  # Not Tax
                },
                {
                    "balance": -6.0,  # Tax
                },
                {
                    "balance": 36.0,
                },
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
        invoice_date = Date.today()
        woff_account = self.cash_discount_writeoff_account
        woff_journal = self.cash_discount_writeoff_journal
        payment_mode = self.payment_mode_out
        payment_mode.post_move = True
        self.company.write(
            {
                "default_cash_discount_writeoff_account_id": woff_account.id,
                "default_cash_discount_writeoff_journal_id": woff_journal.id,
                "cash_discount_base_amount_type": "untaxed",
            }
        )
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
        invoice.ref = "test ref"
        invoice.action_post()

        payment_order = self.create_payment_order(invoice_date, invoice)

        self.assertEqual(len(payment_order.payment_line_ids), 1)
        payment_line = payment_order.payment_line_ids[0]
        self.assertTrue(payment_line.pay_with_discount)
        self.assertAlmostEqual(payment_line.amount_currency, 1770.0)
        self.assertTrue(payment_line.pay_with_discount)

        payment_order.draft2open()
        payment_order.open2generated()
        payment_order.generated2uploaded()

        self.assertEqual(len(payment_order.move_ids), 1)

        self.assertEqual(invoice.payment_state, "paid")

        domain_reconlied_line = payment_order.move_ids.open_reconcile_view()["domain"]
        reconciled_line_ids = self.env["account.move.line"].search(
            domain_reconlied_line
        )

        self.assertRecordValues(
            reconciled_line_ids.sorted(lambda r: r.balance),
            [
                {
                    "balance": -1800.0,
                },
                {
                    "balance": 30.0,
                    "name": "Cash Discount Write-Off",
                },
                {
                    "balance": 1770.0,
                    "name": "test ref",
                },
            ],
        )

        write_off_move = reconciled_line_ids.filtered(
            lambda r: r.journal_id == woff_journal
        ).move_id

        self.assertRecordValues(
            write_off_move.line_ids.sorted(lambda r: r.balance),
            [
                {
                    "balance": -30.0,  # Not Tax
                },
                {
                    "balance": 30.0,
                },
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
        invoice_date = Date.today()
        woff_account = self.cash_discount_writeoff_account
        woff_journal = self.cash_discount_writeoff_journal
        payment_mode = self.payment_mode_out
        payment_mode.post_move = True
        self.company.write(
            {
                "default_cash_discount_writeoff_account_id": woff_account.id,
                "default_cash_discount_writeoff_journal_id": woff_journal.id,
                "cash_discount_base_amount_type": "total",
            }
        )
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
        invoice.ref = "test ref"
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

        payment_order.draft2open()
        payment_order.open2generated()
        payment_order.generated2uploaded()

        self.assertEqual(len(payment_order.move_ids), 1)

        self.assertEqual(invoice.payment_state, "paid")

        domain_reconlied_line = payment_order.move_ids.open_reconcile_view()["domain"]
        reconciled_line_ids = self.env["account.move.line"].search(
            domain_reconlied_line
        )

        self.assertRecordValues(
            reconciled_line_ids.sorted(lambda r: r.balance),
            [
                {
                    "balance": -1800.0,
                },
                {
                    "balance": 24.0,
                    "name": "Cash Discount Write-Off",
                },
                {
                    "balance": 600.0,  # Credit note
                },
                {
                    "balance": 1176.0,
                    "name": "test ref",
                },
            ],
        )

        write_off_move = reconciled_line_ids.filtered(
            lambda r: r.journal_id == woff_journal
        ).move_id

        self.assertRecordValues(
            write_off_move.line_ids.sorted(lambda r: r.balance),
            [
                {
                    "balance": -30.0,  # Not Tax
                },
                {
                    "balance": -6.0,  # Tax
                },
                {
                    "balance": 2.0,  # Tax Credit Note
                },
                {
                    "balance": 10.0,  # Credit Note
                },
                {
                    "balance": 24.0,
                },
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
        invoice_date = Date.today()
        woff_account = self.cash_discount_writeoff_account
        woff_journal = self.cash_discount_writeoff_journal
        payment_mode = self.payment_mode_out
        payment_mode.post_move = True
        self.company.write(
            {
                "default_cash_discount_writeoff_account_id": woff_account.id,
                "default_cash_discount_writeoff_journal_id": woff_journal.id,
                "cash_discount_base_amount_type": "untaxed",
            }
        )
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
        invoice.ref = "test ref"
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

        payment_order.draft2open()
        payment_order.open2generated()
        payment_order.generated2uploaded()

        self.assertEqual(len(payment_order.move_ids), 1)

        self.assertEqual(invoice.payment_state, "paid")

        domain_reconlied_line = payment_order.move_ids.open_reconcile_view()["domain"]
        reconciled_line_ids = self.env["account.move.line"].search(
            domain_reconlied_line
        )

        self.assertRecordValues(
            reconciled_line_ids.sorted(lambda r: r.balance),
            [
                {
                    "balance": -1800.0,
                },
                {
                    "balance": 20.0,
                    "name": "Cash Discount Write-Off",
                },
                {
                    "balance": 600.0,  # Credit Note
                },
                {
                    "balance": 1180.0,
                    "name": "test ref",
                },
            ],
        )

        write_off_move = reconciled_line_ids.filtered(
            lambda r: r.journal_id == woff_journal
        ).move_id

        self.assertRecordValues(
            write_off_move.line_ids.sorted(lambda r: r.balance),
            [
                {
                    "balance": -20.0,  # Not Tax
                },
                {
                    "balance": 20.0,
                },
            ],
        )
