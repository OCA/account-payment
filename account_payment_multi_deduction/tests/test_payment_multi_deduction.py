# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import Command, fields
from odoo.exceptions import UserError
from odoo.tests import Form, tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestPaymentMultiDeduction(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.move_line_model = cls.env["account.move.line"]
        cls.move_model = cls.env["account.move"]
        cls.payment_model = cls.env["account.payment"]
        cls.journal_model = cls.env["account.journal"]
        cls.currency_model = cls.env["res.currency"]
        cls.payment_register_model = cls.env["account.payment.register"]
        cls.register_view_id = "account.view_account_payment_register_form"
        cls.account_expense = cls.company_data["default_account_expense"]

        cls.cust_invoice = cls.init_invoice(
            "out_invoice",
            partner=cls.env.ref("base.res_partner_2"),
            invoice_date=fields.Date.today(),
            post=True,
            amounts=[450.0],
        )

        # New currency, 2X lower
        cls.company_currency = cls.cust_invoice.currency_id
        cls.currency_2x = cls.currency_model.create(
            {
                "name": "2X",  # Foreign currency, 2 time
                "symbol": "X",
                "rate_ids": [
                    Command.create(
                        {
                            "name": fields.Date.today(),
                            "company_rate": cls.company_currency.rate * 2,
                        }
                    )
                ],
            }
        )

    def test_01_one_invoice_payment_fully_paid(self):
        """Validate 1 invoice and make payment with Mark as fully paid"""
        ctx = {
            "active_ids": [self.cust_invoice.id],
            "active_id": self.cust_invoice.id,
            "active_model": "account.move",
        }

        with Form(
            self.payment_register_model.with_context(**ctx),
            view=self.register_view_id,
        ) as f:
            f.amount = 400.0
            f.payment_difference_handling = "reconcile"
            f.writeoff_account_id = self.account_expense
        payment_register = f.save()
        payment = payment_register._create_payments()
        self.assertEqual(payment.state, "paid")

        writeoff = payment.move_id.line_ids.filtered(lambda line: line.is_writeoff)
        self.assertEqual(len(writeoff), 1)
        self.assertEqual(writeoff.account_id, self.account_expense)

    def test_02_one_invoice_multi_deduction_payment(self):
        """Validate 1 invoice and make payment with 2 deduction"""
        ctx = {
            "active_ids": [self.cust_invoice.id],
            "active_id": self.cust_invoice.id,
            "active_model": "account.move",
        }

        # Test deduct only 20.0, throw error
        with self.assertRaisesRegex(UserError, "The total deduction should be 50.0"):
            with Form(
                self.payment_register_model.with_context(**ctx),
                view=self.register_view_id,
            ) as f:
                f.amount = 400.0
                f.payment_difference_handling = "reconcile_multi_deduct"
                with f.deduction_ids.new() as f2:
                    f2.account_id = self.account_expense
                    f2.name = "Expense 1"
                    f2.amount = 20.0
            f.save()

        with Form(
            self.payment_register_model.with_context(**ctx), view=self.register_view_id
        ) as f:
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

        payment_register = f.save()
        payment = payment_register._create_payments()
        self.assertEqual(payment.state, "paid")
        self.assertEqual(self.cust_invoice.payment_state, "paid")

        # Writeoff should create 2
        writeoff = payment.move_id.line_ids.filtered(lambda line: line.is_writeoff)
        self.assertEqual(len(writeoff), 2)
        self.assertEqual(
            writeoff.mapped("account_id"),
            self.account_expense,
        )

    def test_03_one_invoice_payment_foreign_currency(self):
        """Validate 1 invoice and make payment with 2 deduction"""
        # self.cust_invoice.action_post()  # total amount 450.0
        ctx = {
            "active_ids": [self.cust_invoice.id],
            "active_id": self.cust_invoice.id,
            "active_model": "account.move",
        }
        with Form(
            self.payment_register_model.with_context(**ctx), view=self.register_view_id
        ) as f:
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

        payment_register = f.save()
        payment = payment_register._create_payments()
        self.assertEqual(payment.state, "paid")

        self.assertEqual(self.cust_invoice.payment_state, "paid")

        writeoff = payment.move_id.line_ids.filtered(lambda line: line.is_writeoff)
        self.assertEqual(len(writeoff), 2)
        self.assertEqual(
            writeoff.mapped("account_id"),
            self.account_expense,
        )

    def test_04_one_invoice_payment_with_keep_open(self):
        """Validate 1 invoice and make payment with 2 deduction,
        one as normal deduct and another as keep open"""
        ctx = {
            "active_ids": [self.cust_invoice.id],
            "active_id": self.cust_invoice.id,
            "active_model": "account.move",
        }
        with Form(self.payment_register_model.with_context(**ctx)) as f:
            f.amount = 400.0  # Reduce to 400.0, and mark fully paid (multi)
            f.payment_difference_handling = "reconcile_multi_deduct"
            with f.deduction_ids.new() as f2:
                f2.account_id = self.account_expense
                f2.name = "Expense 1"
                f2.amount = 20.0
            with f.deduction_ids.new() as f2:  # Keep Open
                f2.is_open = True
                f2.amount = 30.0
        payment_register = f.save()
        payment = payment_register._create_payments()
        self.assertEqual(payment.state, "in_process")
        payment.action_validate()
        self.assertEqual(payment.state, "paid")
        self.assertEqual(self.cust_invoice.payment_state, "partial")
        self.assertEqual(self.cust_invoice.amount_residual, 30)

        writeoff = payment.move_id.line_ids.filtered(lambda line: line.is_writeoff)
        self.assertEqual(len(writeoff), 1)
        self.assertEqual(writeoff.account_id, self.account_expense)
