# Copyright 2022 ForgeFlow, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import json

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests.common import Form, tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestAccountPaymentLines(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)
        cls.test_product = cls.env["product.product"].create(
            {
                "name": "test_product",
                "type": "service",
            }
        )
        cls.customer = cls.env["res.partner"].create(
            {
                "name": "test_customer",
            }
        )
        cls.customer2 = cls.env["res.partner"].create(
            {
                "name": "test_customer",
            }
        )
        cls.supplier = cls.env["res.partner"].create(
            {
                "name": "test_vendor",
            }
        )
        cls.supplier2 = cls.env["res.partner"].create(
            {
                "name": "test_vendor",
            }
        )
        cls.currency_2x = cls.env["res.currency"].create(
            {
                "name": "2X",  # Foreign currency, 2 time
                "symbol": "X",
                "rate_ids": [
                    (
                        0,
                        0,
                        {
                            "name": fields.Date.today(),
                            "rate": cls.env.company.currency_id.rate * 2,
                        },
                    )
                ],
            }
        )
        cls.payment_terms_split = cls.env["account.payment.term"].create(
            {
                "name": "50% Advance End of Following Month",
                "note": "Payment terms: 30% Advance End of Following Month",
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "value": "percent",
                            "value_amount": 50.0,
                            "sequence": 400,
                            "days": 0,
                            "option": "day_after_invoice_date",
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "value": "balance",
                            "value_amount": 0.0,
                            "sequence": 500,
                            "days": 31,
                            "option": "day_following_month",
                        },
                    ),
                ],
            }
        )

    def setUp(self):
        super().setUp()
        self.bank_journal = self.company_data["default_journal_bank"]
        self.account_receivable = self.company_data["default_account_receivable"]
        self.account_payable = self.company_data["default_account_payable"]
        self.account_expense = self.company_data["default_account_expense"]

    def _create_invoice(
        self, move_type, partner, amount, currency=False, payment_term=False
    ):
        move_form = Form(
            self.env["account.move"].with_context(
                default_move_type=move_type,
            )
        )
        if not currency:
            currency = self.env.company.currency_id
        move_form.invoice_date = fields.Date.today()
        move_form.date = move_form.invoice_date
        move_form.partner_id = partner
        move_form.currency_id = currency
        if payment_term:
            move_form.invoice_payment_term_id = payment_term
        with move_form.invoice_line_ids.new() as line_form:
            line_form.product_id = self.test_product
            line_form.price_unit = amount
            line_form.tax_ids.clear()
        move = move_form.save()
        move.action_post()
        return move

    def _create_refund(self, invoice, refund_method="cancel"):
        ctx = {"active_model": "account.move", "active_ids": [invoice.id]}
        move_reversal = (
            self.env["account.move.reversal"]
            .with_context(**ctx)
            .create(
                {
                    "date": fields.Date.today(),
                    "reason": "no reason",
                    "refund_method": refund_method,
                    "journal_id": invoice.journal_id.id,
                }
            )
        )
        reversal = move_reversal.reverse_moves()
        reverse_move = self.env["account.move"].browse(reversal["res_id"])
        return reverse_move

    def _create_payment(
        self,
        main_partner,
        total_amount,
        payment_type,
        partner_type,
        lines=False,
        currency=False,
        post=False,
        suggest_payment_distribution=False,
        writeoff_account=False,
    ):
        payment_form = Form(
            self.env["account.payment"].with_context(
                default_journal_id=self.bank_journal.id
            )
        )
        payment_form.partner_id = main_partner
        payment_form.payment_type = payment_type
        payment_form.partner_type = partner_type
        payment_form.amount = total_amount
        if writeoff_account:
            payment_form.writeoff_account_id = writeoff_account
        if not currency:
            currency = self.env.company.currency_id
        payment_form.currency_id = currency
        if not lines:
            lines = []
        for line in lines:
            with payment_form.line_payment_counterpart_ids.new() as line_form:
                if line.get("move_id", False):
                    line_form.move_id = line.get("move_id", False)
                if line.get("account_id", False):
                    line_form.account_id = line.get("account_id", False)
                if line.get("amount", False):
                    line_form.amount = line.get("amount", False)
                if line.get("fully_paid", False):
                    line_form.fully_paid = line.get("fully_paid", False)
                if line.get("writeoff_account_id", False):
                    line_form.writeoff_account_id = line.get(
                        "writeoff_account_id", False
                    )
        payment = payment_form.save()
        if suggest_payment_distribution:
            payment.action_propose_payment_distribution()
        if post:
            payment.action_post()
        return payment

    def test_01_customer_payment(self):
        new_invoice = self._create_invoice("out_invoice", self.customer, 100.0)
        self.assertEqual(new_invoice.payment_state, "not_paid")
        self.assertEqual(new_invoice.amount_total, 100.0)
        new_payment = self._create_payment(
            self.customer,
            100.0,
            "inbound",
            "customer",
            [
                {
                    "move_id": new_invoice,
                }
            ],
            post=True,
        )
        self.assertEqual(new_payment.state, "posted")
        self.assertTrue(new_payment.is_reconciled)
        self.assertEqual(new_payment.reconciled_invoice_ids, new_invoice)

        new_invoice2 = self._create_invoice("out_invoice", self.customer, 100.0)
        self.assertEqual(new_invoice2.payment_state, "not_paid")
        self.assertEqual(new_invoice2.amount_total, 100.0)
        new_payment2 = self._create_payment(
            self.customer,
            50.0,
            "inbound",
            "customer",
            [
                {
                    "move_id": new_invoice2,
                    "amount": 50.0,
                }
            ],
            post=True,
        )
        self.assertEqual(new_payment2.state, "posted")
        self.assertTrue(new_payment2.is_reconciled)
        self.assertEqual(new_payment2.reconciled_invoice_ids, new_invoice2)
        self.assertEqual(new_invoice2.amount_residual, 50.0)

        new_payment3 = self._create_payment(
            self.customer,
            50.0,
            "inbound",
            "customer",
            [
                {
                    "move_id": new_invoice2,
                }
            ],
            post=True,
        )
        self.assertEqual(new_payment3.state, "posted")
        self.assertTrue(new_payment3.is_reconciled)
        self.assertEqual(new_payment3.reconciled_invoice_ids, new_invoice2)
        self.assertEqual(new_invoice2.amount_residual, 0.0)

        new_payment2.action_draft()
        new_payment2.action_cancel()

        self.assertEqual(new_payment2.state, "cancel")
        self.assertEqual(new_payment3.state, "posted")
        self.assertTrue(new_payment3.is_reconciled)
        self.assertEqual(new_payment3.reconciled_invoice_ids, new_invoice2)
        self.assertEqual(new_invoice2.amount_residual, 50.0)

    def test_02_customer_refund_payment(self):
        new_invoice = self._create_invoice("out_invoice", self.customer, 100.0)
        new_invoice2 = self._create_invoice("out_invoice", self.customer, 100.0)
        self.assertEqual(new_invoice.payment_state, "not_paid")
        self.assertEqual(new_invoice.amount_total, 100.0)
        self.assertEqual(new_invoice2.payment_state, "not_paid")
        self.assertEqual(new_invoice2.amount_total, 100.0)
        new_payment = self._create_payment(
            self.customer,
            200.0,
            "inbound",
            "customer",
            [
                {
                    "move_id": new_invoice,
                },
                {
                    "move_id": new_invoice2,
                },
            ],
            post=True,
        )
        self.assertEqual(new_payment.state, "posted")
        self.assertTrue(new_payment.is_reconciled)
        self.assertEqual(new_payment.reconciled_invoice_ids, new_invoice + new_invoice2)
        self.assertIn(new_invoice.payment_state, ["paid", "in_payment"])
        self.assertIn(new_invoice2.payment_state, ["paid", "in_payment"])

        new_refund = self._create_refund(new_invoice, "refund")
        new_refund.action_post()
        self.assertEqual(new_refund.payment_state, "not_paid")
        self.assertEqual(new_refund.amount_total, 100.0)
        new_payment_refund = self._create_payment(
            self.customer,
            100.0,
            "outbound",
            "customer",
            [
                {
                    "move_id": new_refund,
                },
            ],
            post=True,
        )
        self.assertEqual(new_payment_refund.state, "posted")
        self.assertTrue(new_payment_refund.is_reconciled)
        self.assertEqual(new_payment_refund.reconciled_invoice_ids, new_refund)
        self.assertIn(new_refund.payment_state, ["paid", "in_payment"])

    def test_03_supplier_payment(self):
        new_invoice = self._create_invoice("in_invoice", self.supplier, 100.0)
        self.assertEqual(new_invoice.payment_state, "not_paid")
        self.assertEqual(new_invoice.amount_total, 100.0)
        new_payment = self._create_payment(
            self.supplier,
            100.0,
            "outbound",
            "supplier",
            [
                {
                    "move_id": new_invoice,
                }
            ],
            post=True,
        )
        self.assertEqual(new_payment.state, "posted")
        self.assertTrue(new_payment.is_reconciled)
        self.assertEqual(new_payment.reconciled_bill_ids, new_invoice)

        new_invoice2 = self._create_invoice("in_invoice", self.supplier, 100.0)
        self.assertEqual(new_invoice2.payment_state, "not_paid")
        self.assertEqual(new_invoice2.amount_total, 100.0)
        new_payment2 = self._create_payment(
            self.supplier,
            50.0,
            "outbound",
            "supplier",
            [
                {
                    "move_id": new_invoice2,
                    "amount": 50.0,
                }
            ],
            post=True,
        )
        self.assertEqual(new_payment2.state, "posted")
        self.assertTrue(new_payment2.is_reconciled)
        self.assertEqual(new_payment2.reconciled_bill_ids, new_invoice2)
        self.assertEqual(new_invoice2.amount_residual, 50.0)

        new_payment3 = self._create_payment(
            self.supplier,
            50.0,
            "outbound",
            "supplier",
            [
                {
                    "move_id": new_invoice2,
                }
            ],
            post=True,
        )
        self.assertEqual(new_payment3.state, "posted")
        self.assertTrue(new_payment3.is_reconciled)
        self.assertEqual(new_payment3.reconciled_bill_ids, new_invoice2)
        self.assertEqual(new_invoice2.amount_residual, 0.0)

        new_payment2.action_draft()
        new_payment2.action_cancel()

        self.assertEqual(new_payment2.state, "cancel")
        self.assertEqual(new_payment3.state, "posted")
        self.assertTrue(new_payment3.is_reconciled)
        self.assertEqual(new_payment3.reconciled_bill_ids, new_invoice2)
        self.assertEqual(new_invoice2.amount_residual, 50.0)

    def test_04_supplier_refund_payment(self):
        new_invoice = self._create_invoice("in_invoice", self.supplier, 100.0)
        new_invoice2 = self._create_invoice("in_invoice", self.supplier, 100.0)
        self.assertEqual(new_invoice.payment_state, "not_paid")
        self.assertEqual(new_invoice.amount_total, 100.0)
        self.assertEqual(new_invoice2.payment_state, "not_paid")
        self.assertEqual(new_invoice2.amount_total, 100.0)
        new_payment = self._create_payment(
            self.supplier,
            200.0,
            "outbound",
            "supplier",
            [
                {
                    "move_id": new_invoice,
                },
                {
                    "move_id": new_invoice2,
                },
            ],
            post=True,
        )
        self.assertEqual(new_payment.state, "posted")
        self.assertTrue(new_payment.is_reconciled)
        self.assertEqual(new_payment.reconciled_bill_ids, new_invoice + new_invoice2)
        self.assertIn(new_invoice.payment_state, ["paid", "in_payment"])
        self.assertIn(new_invoice2.payment_state, ["paid", "in_payment"])

        new_refund = self._create_refund(new_invoice, "refund")
        new_refund.action_post()
        self.assertEqual(new_refund.payment_state, "not_paid")
        self.assertEqual(new_refund.amount_total, 100.0)
        new_payment_refund = self._create_payment(
            self.supplier,
            100.0,
            "inbound",
            "supplier",
            [
                {
                    "move_id": new_refund,
                },
            ],
            post=True,
        )
        self.assertEqual(new_payment_refund.state, "posted")
        self.assertTrue(new_payment_refund.is_reconciled)
        self.assertEqual(new_payment_refund.reconciled_bill_ids, new_refund)
        self.assertIn(new_refund.payment_state, ["paid", "in_payment"])

    def test_05_partial_payments(self):
        new_invoice = self._create_invoice("out_invoice", self.customer, 100.0)
        new_invoice2 = self._create_invoice("out_invoice", self.customer, 100.0)
        new_invoice3 = self._create_invoice(
            "out_invoice", self.customer, 100.0, payment_term=self.payment_terms_split
        )
        self.assertEqual(new_invoice.payment_state, "not_paid")
        self.assertEqual(new_invoice.amount_total, 100.0)
        self.assertEqual(new_invoice2.payment_state, "not_paid")
        self.assertEqual(new_invoice2.amount_total, 100.0)
        self.assertEqual(new_invoice3.payment_state, "not_paid")
        self.assertEqual(new_invoice3.amount_total, 100.0)
        self.assertEqual(
            len(
                new_invoice3.line_ids.filtered(
                    lambda x: x.partner_id.id == new_invoice3.partner_id.id
                    and x.account_id.user_type_id.type == "receivable"
                )
            ),
            2,
        )
        new_payment = self._create_payment(
            self.customer,
            150.0,
            "inbound",
            "customer",
            [
                {
                    "move_id": new_invoice,
                    "amount": 50.0,
                },
                {
                    "move_id": new_invoice2,
                    "amount": 50.0,
                },
                {
                    "move_id": new_invoice3,
                    "amount": 50.0,
                },
            ],
            post=True,
        )
        self.assertEqual(new_invoice.payment_state, "partial")
        self.assertEqual(new_invoice.amount_residual, 50.0)
        self.assertEqual(new_invoice2.payment_state, "partial")
        self.assertEqual(new_invoice2.amount_residual, 50.0)
        self.assertEqual(new_invoice3.payment_state, "partial")
        self.assertEqual(new_invoice3.amount_residual, 50.0)
        self.assertEqual(new_payment.state, "posted")
        self.assertTrue(new_payment.is_reconciled)
        self.assertEqual(
            new_payment.reconciled_invoice_ids,
            new_invoice + new_invoice2 + new_invoice3,
        )

        new_payment2 = self._create_payment(
            self.customer,
            100.0,
            "inbound",
            "customer",
            [
                {
                    "move_id": new_invoice,
                    "amount": 50.0,
                },
                {
                    "move_id": new_invoice2,
                    "amount": 50.0,
                },
            ],
            post=True,
        )
        self.assertIn(new_invoice.payment_state, ["paid", "in_payment"])
        self.assertEqual(new_invoice.amount_residual, 0.0)
        self.assertIn(new_invoice2.payment_state, ["paid", "in_payment"])
        self.assertEqual(new_invoice2.amount_residual, 0.0)
        self.assertEqual(new_invoice3.payment_state, "partial")
        self.assertEqual(new_invoice3.amount_residual, 50.0)
        self.assertEqual(new_payment2.state, "posted")
        self.assertTrue(new_payment2.is_reconciled)
        self.assertEqual(
            new_payment2.reconciled_invoice_ids,
            new_invoice + new_invoice2,
        )
        new_payment3 = self._create_payment(
            self.customer,
            50.0,
            "inbound",
            "customer",
            [
                {
                    "move_id": new_invoice3,
                    "amount": 50.0,
                },
            ],
            post=True,
        )
        self.assertIn(new_invoice3.payment_state, ["paid", "in_payment"])
        self.assertEqual(new_invoice3.amount_residual, 0.0)
        self.assertEqual(new_payment3.state, "posted")
        self.assertTrue(new_payment3.is_reconciled)
        self.assertEqual(
            new_payment3.reconciled_invoice_ids,
            new_invoice3,
        )

    def test_06_payments_without_invoices(self):
        new_payment = self._create_payment(
            self.customer,
            100.0,
            "inbound",
            "customer",
            [
                {
                    "account_id": self.account_expense,
                    "amount": 50.0,
                },
                {
                    "account_id": self.customer.property_account_receivable_id,
                    "amount": 50.0,
                },
            ],
            post=True,
        )
        self.assertEqual(new_payment.state, "posted")
        self.assertFalse(new_payment.is_reconciled)
        self.assertFalse(bool(new_payment.reconciled_invoice_ids))
        new_invoice = self._create_invoice("out_invoice", self.customer, 100.0)
        payments = json.loads(new_invoice.invoice_outstanding_credits_debits_widget)
        self.assertEqual(sum(p.get("amount") for p in payments.get("content")), 50)
        new_invoice.js_assign_outstanding_line(payments.get("content", [])[0].get("id"))
        self.assertEqual(new_invoice.payment_state, "partial")
        self.assertEqual(new_invoice.amount_residual, 50.0)
        self.assertEqual(new_payment.state, "posted")
        self.assertTrue(new_payment.is_reconciled)
        self.assertEqual(
            new_payment.reconciled_invoice_ids,
            new_invoice,
        )

    def test_07_payment_multi_currency(self):
        new_invoice = self._create_invoice(
            "out_invoice", self.customer, 100.0, currency=self.currency_2x
        )
        self.assertEqual(new_invoice.payment_state, "not_paid")
        self.assertEqual(new_invoice.amount_total, 100.0)
        new_payment = self._create_payment(
            self.customer,
            50.0,
            "inbound",
            "customer",
            [
                {
                    "move_id": new_invoice,
                    "amount": 50.0,
                },
            ],
            post=True,
        )
        self.assertIn(new_invoice.payment_state, ["paid", "in_payment"])
        self.assertEqual(new_invoice.amount_residual, 0.0)
        self.assertEqual(new_payment.state, "posted")
        self.assertTrue(new_payment.is_reconciled)
        self.assertEqual(
            new_payment.reconciled_invoice_ids,
            new_invoice,
        )

        new_invoice2 = self._create_invoice(
            "out_invoice", self.customer, 100.0, currency=self.currency_2x
        )
        self.assertEqual(new_invoice2.payment_state, "not_paid")
        self.assertEqual(new_invoice2.amount_total, 100.0)
        new_payment2 = self._create_payment(
            self.customer,
            100.0,
            "inbound",
            "customer",
            [
                {
                    "move_id": new_invoice2,
                    "amount": 100.0,
                },
            ],
            post=True,
            currency=self.currency_2x,
        )
        self.assertIn(new_invoice2.payment_state, ["paid", "in_payment"])
        self.assertEqual(new_invoice2.amount_residual, 0.0)
        self.assertEqual(new_payment2.state, "posted")
        self.assertTrue(new_payment2.is_reconciled)
        self.assertEqual(
            new_payment2.reconciled_invoice_ids,
            new_invoice2,
        )

        new_invoice = self._create_invoice("out_invoice", self.customer, 100.0)
        self.assertEqual(new_invoice.payment_state, "not_paid")
        self.assertEqual(new_invoice.amount_total, 100.0)
        new_payment = self._create_payment(
            self.customer,
            200.0,
            "inbound",
            "customer",
            [
                {
                    "move_id": new_invoice,
                    "amount": 200.0,
                },
            ],
            post=True,
            currency=self.currency_2x,
        )
        self.assertIn(new_invoice.payment_state, ["paid", "in_payment"])
        self.assertEqual(new_invoice.amount_residual, 0.0)
        self.assertEqual(new_payment.state, "posted")
        self.assertTrue(new_payment.is_reconciled)
        self.assertEqual(
            new_payment.reconciled_invoice_ids,
            new_invoice,
        )

    def test_08_payment_term_split(self):
        new_invoice = self._create_invoice("out_invoice", self.customer, 100.0)
        new_invoice2 = self._create_invoice("out_invoice", self.customer, 100.0)
        new_invoice3 = self._create_invoice(
            "out_invoice", self.customer, 100.0, payment_term=self.payment_terms_split
        )
        self.assertEqual(new_invoice.payment_state, "not_paid")
        self.assertEqual(new_invoice.amount_total, 100.0)
        self.assertEqual(new_invoice2.payment_state, "not_paid")
        self.assertEqual(new_invoice2.amount_total, 100.0)
        self.assertEqual(new_invoice3.payment_state, "not_paid")
        self.assertEqual(new_invoice3.amount_total, 100.0)
        new_payment = self._create_payment(
            self.customer,
            300.0,
            "inbound",
            "customer",
            suggest_payment_distribution=True,
        )
        self.assertEqual(len(new_payment.line_payment_counterpart_ids), 4)
        self.assertEqual(
            len(
                new_payment.line_payment_counterpart_ids.filtered(
                    lambda x: x.amount == 50.0
                )
            ),
            2,
        )
        self.assertEqual(
            len(
                new_payment.line_payment_counterpart_ids.filtered(
                    lambda x: x.amount == 100.0
                )
            ),
            2,
        )
        new_payment.action_post()
        self.assertIn(new_invoice.payment_state, ["paid", "in_payment"])
        self.assertEqual(new_invoice.amount_residual, 0.0)
        self.assertIn(new_invoice2.payment_state, ["paid", "in_payment"])
        self.assertEqual(new_invoice2.amount_residual, 0.0)
        self.assertIn(new_invoice3.payment_state, ["paid", "in_payment"])
        self.assertEqual(new_invoice3.amount_residual, 0.0)
        self.assertEqual(new_payment.state, "posted")
        self.assertTrue(new_payment.is_reconciled)
        self.assertEqual(
            new_payment.reconciled_invoice_ids,
            new_invoice + new_invoice2 + new_invoice3,
        )

    def test_09_offset_payment(self):
        new_invoice = self._create_invoice("out_invoice", self.customer, 100.0)
        self.assertEqual(new_invoice.payment_state, "not_paid")
        self.assertEqual(new_invoice.amount_total, 100.0)
        new_payment = self._create_payment(
            self.customer,
            50.0,
            "inbound",
            "customer",
            [
                {
                    "move_id": new_invoice,
                    "amount": 50.0,
                    "fully_paid": True,
                },
            ],
            writeoff_account=self.account_expense,
            post=True,
        )
        self.assertIn(new_invoice.payment_state, ["paid", "in_payment"])
        self.assertEqual(new_invoice.amount_residual, 0.0)
        self.assertEqual(new_payment.state, "posted")
        self.assertTrue(new_payment.is_reconciled)
        self.assertEqual(
            new_payment.reconciled_invoice_ids,
            new_invoice,
        )

        new_invoice2 = self._create_invoice("out_invoice", self.customer, 100.0)
        new_invoice3 = self._create_invoice("out_invoice", self.customer, 100.0)
        self.assertEqual(new_invoice2.payment_state, "not_paid")
        self.assertEqual(new_invoice2.amount_total, 100.0)
        self.assertEqual(new_invoice3.payment_state, "not_paid")
        self.assertEqual(new_invoice3.amount_total, 100.0)
        new_payment2 = self._create_payment(
            self.customer,
            150.0,
            "inbound",
            "customer",
            [
                {
                    "move_id": new_invoice2,
                    "amount": 50.0,
                    "writeoff_account_id": self.account_expense,
                    "fully_paid": True,
                },
                {
                    "move_id": new_invoice3,
                    "amount": 100.0,
                },
            ],
        )
        writeoff_line = new_payment2.line_payment_counterpart_ids.filtered(
            lambda x: x.move_id == new_invoice2
        )
        self.assertEqual(writeoff_line.writeoff_amount, 50.0)
        self.assertEqual(writeoff_line.residual_after_payment, 0.0)
        new_payment2.action_post()
        self.assertIn(new_invoice2.payment_state, ["paid", "in_payment"])
        self.assertEqual(new_invoice2.amount_residual, 0.0)
        self.assertIn(new_invoice3.payment_state, ["paid", "in_payment"])
        self.assertEqual(new_invoice3.amount_residual, 0.0)
        self.assertEqual(new_payment2.state, "posted")
        self.assertTrue(new_payment2.is_reconciled)
        self.assertEqual(
            new_payment2.reconciled_invoice_ids,
            new_invoice2 + new_invoice3,
        )

    def test_10_payment_distribution_proposition(self):
        new_out_invoice = self._create_invoice("out_invoice", self.customer, 100.0)
        new_out_refund = self._create_invoice("out_refund", self.customer, 100.0)
        new_in_invoice = self._create_invoice("in_invoice", self.customer, 100.0)
        new_in_refund = self._create_invoice("in_refund", self.customer, 100.0)
        new_out_invoice2 = self._create_invoice("out_invoice", self.customer2, 100.0)
        new_out_refund2 = self._create_invoice("out_refund", self.customer2, 100.0)
        new_in_invoice2 = self._create_invoice("in_invoice", self.customer2, 100.0)
        new_in_refund2 = self._create_invoice("in_refund", self.customer2, 100.0)

        payment_form = Form(
            self.env["account.payment"].with_context(
                default_journal_id=self.bank_journal.id
            )
        )
        payment_form.partner_id = self.customer
        payment_form.payment_type = "inbound"
        payment_form.partner_type = "customer"
        payment_form.amount = 50.0
        payment = payment_form.save()
        payment.action_propose_payment_distribution()
        self.assertEqual(len(payment.line_payment_counterpart_ids), 1)
        self.assertEqual(
            sum(payment.line_payment_counterpart_ids.mapped("amount")), 50.0
        )
        self.assertEqual(
            payment.line_payment_counterpart_ids.mapped("move_id"), new_out_invoice
        )

        payment.action_delete_counterpart_lines()
        self.assertEqual(len(payment.line_payment_counterpart_ids), 0)

        payment.action_propose_payment_distribution()
        payment.action_post()
        self.assertEqual(new_out_invoice.payment_state, "partial")
        self.assertEqual(new_out_invoice.amount_residual, 50.0)
        self.assertEqual(payment.state, "posted")
        self.assertTrue(payment.is_reconciled)
        self.assertEqual(
            payment.reconciled_invoice_ids,
            new_out_invoice,
        )

        new_payment2 = self._create_payment(
            self.customer,
            50.0,
            "outbound",
            "customer",
            [
                {
                    "move_id": new_out_invoice,
                    "amount": -50.0,
                },
                {
                    "move_id": new_out_refund,
                    "amount": 100.0,
                },
            ],
            post=True,
        )
        self.assertIn(new_out_invoice.payment_state, ["paid", "in_payment"])
        self.assertEqual(new_out_invoice.amount_residual, 0.0)
        self.assertIn(new_out_refund.payment_state, ["paid", "in_payment"])
        self.assertEqual(new_out_refund.amount_residual, 0.0)
        self.assertEqual(new_payment2.state, "posted")
        self.assertTrue(new_payment2.is_reconciled)
        self.assertEqual(
            new_payment2.reconciled_invoice_ids,
            new_out_invoice + new_out_refund,
        )

        payment_form = Form(
            self.env["account.payment"].with_context(
                default_journal_id=self.bank_journal.id
            )
        )
        payment_form.partner_id = self.customer2
        payment_form.payment_type = "outbound"
        payment_form.partner_type = "customer"
        payment_form.amount = 100.0
        payment = payment_form.save()
        payment.action_propose_payment_distribution()
        self.assertEqual(len(payment.line_payment_counterpart_ids), 1)
        self.assertEqual(
            sum(payment.line_payment_counterpart_ids.mapped("amount")), 100.0
        )
        self.assertEqual(
            payment.line_payment_counterpart_ids.mapped("move_id"), new_out_refund2
        )

        payment.action_delete_counterpart_lines()
        self.assertEqual(len(payment.line_payment_counterpart_ids), 0)
        payment.write(
            {
                "payment_type": "outbound",
                "partner_type": "supplier",
            }
        )
        payment.action_propose_payment_distribution()
        self.assertEqual(len(payment.line_payment_counterpart_ids), 1)
        self.assertEqual(
            sum(payment.line_payment_counterpart_ids.mapped("amount")), 100.0
        )
        self.assertEqual(
            payment.line_payment_counterpart_ids.mapped("move_id"), new_in_invoice2
        )

        payment.action_delete_counterpart_lines()
        self.assertEqual(len(payment.line_payment_counterpart_ids), 0)
        payment.write(
            {
                "payment_type": "inbound",
                "partner_type": "supplier",
            }
        )
        payment.action_propose_payment_distribution()
        self.assertEqual(len(payment.line_payment_counterpart_ids), 1)
        self.assertEqual(
            sum(payment.line_payment_counterpart_ids.mapped("amount")), 100.0
        )
        self.assertEqual(
            payment.line_payment_counterpart_ids.mapped("move_id"), new_in_refund2
        )
        payment.unlink()

        new_payment3 = self._create_payment(
            self.customer,
            0.0,
            "outbound",
            "supplier",
            [
                {
                    "move_id": new_in_refund,
                    "amount": -100.0,
                },
                {
                    "move_id": new_in_invoice,
                    "amount": 100.0,
                },
            ],
            post=True,
        )
        self.assertIn(new_in_refund.payment_state, ["paid", "in_payment"])
        self.assertEqual(new_in_refund.amount_residual, 0.0)
        self.assertIn(new_in_invoice.payment_state, ["paid", "in_payment"])
        self.assertEqual(new_in_invoice.amount_residual, 0.0)
        self.assertEqual(new_payment3.state, "posted")
        self.assertTrue(new_payment3.is_reconciled)
        self.assertEqual(
            new_payment3.reconciled_bill_ids,
            new_in_refund + new_in_invoice,
        )

        new_payment4 = self._create_payment(
            self.customer2,
            0.0,
            "inbound",
            "customer",
            [
                {
                    "move_id": new_out_refund2,
                    "amount": -100.0,
                },
                {
                    "move_id": new_out_invoice2,
                    "amount": 100.0,
                },
                {
                    "move_id": new_in_refund2,
                    "amount": 100.0,
                },
                {
                    "move_id": new_in_invoice2,
                    "amount": -100.0,
                },
            ],
            post=True,
        )
        self.assertIn(new_out_refund2.payment_state, ["paid", "in_payment"])
        self.assertEqual(new_out_refund2.amount_residual, 0.0)
        self.assertIn(new_out_invoice2.payment_state, ["paid", "in_payment"])
        self.assertEqual(new_out_invoice2.amount_residual, 0.0)
        self.assertIn(new_in_refund2.payment_state, ["paid", "in_payment"])
        self.assertEqual(new_in_refund2.amount_residual, 0.0)
        self.assertIn(new_in_invoice2.payment_state, ["paid", "in_payment"])
        self.assertEqual(new_in_invoice2.amount_residual, 0.0)
        self.assertEqual(new_payment4.state, "posted")
        self.assertTrue(new_payment4.is_reconciled)
        self.assertEqual(
            new_payment4.reconciled_invoice_ids,
            new_out_invoice2 + new_out_refund2,
        )
        self.assertEqual(
            new_payment4.reconciled_bill_ids,
            new_in_refund2 + new_in_invoice2,
        )

    def test_11_exceptions(self):
        new_out_invoice = self._create_invoice("out_invoice", self.customer, 100.0)

        # Should select a writeoff_account
        with self.assertRaises(ValidationError):
            self._create_payment(
                self.customer,
                50.0,
                "inbound",
                "customer",
                [
                    {
                        "move_id": new_out_invoice,
                        "amount": 50.0,
                        "fully_paid": True,
                    },
                ],
                post=True,
            )

        # Should input lower or equal amount than invoice selected in line
        with self.assertRaises(ValidationError):
            self._create_payment(
                self.customer,
                150.0,
                "inbound",
                "customer",
                [
                    {
                        "move_id": new_out_invoice,
                        "amount": 150.0,
                    },
                ],
                post=True,
            )
