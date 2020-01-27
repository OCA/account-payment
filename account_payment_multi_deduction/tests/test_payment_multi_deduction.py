# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import Form, SavepointCase


class TestPaymentMultiDeduction(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestPaymentMultiDeduction, cls).setUpClass()

        cls.partner = cls.env.ref("base.res_partner_12")
        cls.account_receivable = cls.partner.property_account_receivable_id
        cls.account_revenue = cls.env["account.account"].search(
            [
                (
                    "user_type_id",
                    "=",
                    cls.env.ref("account.data_account_type_revenue").id,
                )
            ],
            limit=1,
        )
        cls.account_expense = cls.env["account.account"].search(
            [
                (
                    "user_type_id",
                    "=",
                    cls.env.ref("account.data_account_type_expenses").id,
                )
            ],
            limit=1,
        )

        cls.cust_invoice = cls.env["account.move"].create(
            {
                "name": "Test Customer Invoice",
                "type": "out_invoice",
                "journal_id": cls.env["account.journal"]
                .search([("type", "=", "sale")], limit=1)
                .id,
                "partner_id": cls.env.ref("base.res_partner_12").id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.env.ref("product.product_product_3").id,
                            "quantity": 1.0,
                            "account_id": cls.account_revenue.id,
                            "name": "[PCSC234] PC Assemble SC234",
                            "price_unit": 450.00,
                        },
                    )
                ],
            }
        )

        # New currency, 2X lower
        cls.company_currency = cls.cust_invoice.currency_id
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
                            "rate": cls.company_currency.rate * 2,
                        },
                    )
                ],
            }
        )

    def test_one_invoice_payment(self):
        """ Validate 1 invoice and make payment with 2 deduction """
        self.cust_invoice.post()  # total amount 450.0
        ctx = {
            "active_ids": [self.cust_invoice.id],
            "active_id": self.cust_invoice.id,
            "active_model": "account.move",
        }
        PaymentWizard = self.env["account.payment"]
        view_id = "account_payment_multi_deduction." "view_account_payment_form"
        with self.assertRaises(UserError):  # Deduct only 20.0, throw error
            with Form(PaymentWizard.with_context(ctx), view=view_id) as f:
                f.amount = 400.0
                f.payment_difference_handling = "reconcile_multi_deduct"
                with f.deduction_ids.new() as f2:
                    f2.account_id = self.account_expense
                    f2.name = "Expense 1"
                    f2.amount = 20.0
            f.save()

        with Form(PaymentWizard.with_context(ctx), view=view_id) as f:
            f.amount = 400.0  # Reduce to 400.0, and mark fully paid (multi)
            f.payment_difference_handling = "reconcile_multi_deduct"
            with f.deduction_ids.new() as f2:
                f2.account_id = self.account_expense
                f2.name = "Expense 1"
                f2.amount = 20.0
            with f.deduction_ids.new() as f2:
                f2.account_id = self.account_expense
                f2.name = "Expense 2"
                f2.amount = 30.0

        payment = f.save()
        payment.post()

        self.assertEqual(payment.state, "posted")

        move_lines = self.env["account.move.line"].search(
            [("payment_id", "=", payment.id)]
        )
        bank_account = (
            payment.journal_id.default_debit_account_id
            or payment.journal_id.default_credit_account_id
        )

        self.assertEqual(self.cust_invoice.invoice_payment_state, "paid")
        self.assertRecordValues(
            move_lines,
            [
                {
                    "account_id": self.account_receivable.id,
                    "debit": 0.0,
                    "credit": 450.0,
                },
                {"account_id": bank_account.id, "debit": 400.0, "credit": 0.0},
                {
                    "account_id": self.account_expense.id,
                    "name": "Expense 1",
                    "debit": 20.0,
                    "credit": 0.0,
                },
                {
                    "account_id": self.account_expense.id,
                    "name": "Expense 2",
                    "debit": 30.0,
                    "credit": 0.0,
                },
            ],
        )

    def test_one_invoice_payment_foreign_currency(self):
        """ Validate 1 invoice and make payment with 2 deduction """
        self.cust_invoice.post()  # total amount 450.0
        ctx = {
            "active_ids": [self.cust_invoice.id],
            "active_id": self.cust_invoice.id,
            "active_model": "account.move",
        }
        PaymentWizard = self.env["account.payment"]
        view_id = "account_payment_multi_deduction." "view_account_payment_form"

        with Form(PaymentWizard.with_context(ctx), view=view_id) as f:
            f.currency_id = self.currency_2x
            f.amount = 800.0  # 400 -> 800 as we use currency 2x
            f.payment_difference_handling = "reconcile_multi_deduct"
            with f.deduction_ids.new() as f2:
                f2.account_id = self.account_expense
                f2.name = "Expense 1"
                f2.amount = 40.0  # 20 -> 40
            with f.deduction_ids.new() as f2:
                f2.account_id = self.account_expense
                f2.name = "Expense 2"
                f2.amount = 60.0  # 60 -> 80

        payment = f.save()
        payment.post()

        self.assertEqual(payment.state, "posted")

        move_lines = self.env["account.move.line"].search(
            [("payment_id", "=", payment.id)]
        )
        bank_account = (
            payment.journal_id.default_debit_account_id
            or payment.journal_id.default_credit_account_id
        )

        self.assertEqual(self.cust_invoice.invoice_payment_state, "paid")
        self.assertRecordValues(
            move_lines,
            [
                {
                    "account_id": self.account_receivable.id,
                    "debit": 0.0,
                    "credit": 450.0,
                    "amount_currency": -900.0,
                    "currency_id": self.currency_2x.id,
                },
                {
                    "account_id": bank_account.id,
                    "debit": 400.0,
                    "credit": 0.0,
                    "amount_currency": 800.0,
                    "currency_id": self.currency_2x.id,
                },
                {
                    "account_id": self.account_expense.id,
                    "name": "Expense 1",
                    "debit": 20.0,
                    "credit": 0.0,
                    "amount_currency": 40.0,
                    "currency_id": self.currency_2x.id,
                },
                {
                    "account_id": self.account_expense.id,
                    "name": "Expense 2",
                    "debit": 30.0,
                    "credit": 0.0,
                    "amount_currency": 60.0,
                    "currency_id": self.currency_2x.id,
                },
            ],
        )
