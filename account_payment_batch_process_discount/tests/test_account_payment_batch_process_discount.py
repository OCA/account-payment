# Copyright 2024 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from datetime import datetime, timedelta

from odoo import Command
from odoo.tests.common import Form, TransactionCase


class TestAccountPaymentBatchProcessDiscount(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env.ref("base.res_partner_2")
        cls.vendor = cls.env.ref("base.res_partner_3")
        cls.sale_journal = cls.env["account.journal"].search(
            [("type", "=", "sale")], limit=1
        )
        cls.purchase_journal = cls.env["account.journal"].search(
            [("type", "=", "purchase")], limit=1
        )
        cls.account_revenue = cls.env["account.account"].search(
            [
                ("account_type", "=", "income"),
                ("company_id", "=", cls.env.company.id),
            ],
            limit=1,
        )
        cls.account_expense = cls.env["account.account"].search(
            [
                ("account_type", "=", "expense"),
                ("company_id", "=", cls.env.company.id),
            ],
            limit=1,
        )

        cls.payment_term = cls.env["account.payment.term"].create(
            {
                "name": "15 Days",
                "is_discount": True,
                "line_ids": [
                    Command.create(
                        {
                            "value": "balance",
                            "days": 15,
                            "discount_percentage": 10,
                            "discount_days": 10,
                            "discount_expense_account_id": cls.account_expense.id,
                            "discount_income_account_id": cls.account_revenue.id,
                        },
                    )
                ],
            }
        )

        cls.cust_invoice_1 = cls.env["account.move"].create(
            {
                "name": "Test Customer Invoice 1",
                "move_type": "out_invoice",
                "journal_id": cls.sale_journal.id,
                "partner_id": cls.partner.id,
                "invoice_payment_term_id": cls.payment_term.id,
                "invoice_line_ids": [
                    Command.create(
                        {
                            "product_id": cls.env.ref("product.product_product_3").id,
                            "quantity": 1.0,
                            "price_unit": 100,
                            "account_id": cls.account_revenue.id,
                            "tax_ids": False,
                        },
                    )
                ],
            }
        )

        cls.cust_invoice_2 = cls.env["account.move"].create(
            {
                "name": "Test Customer Invoice 2",
                "move_type": "out_invoice",
                "journal_id": cls.sale_journal.id,
                "partner_id": cls.partner.id,
                "invoice_payment_term_id": cls.payment_term.id,
                "invoice_line_ids": [
                    Command.create(
                        {
                            "product_id": cls.env.ref("product.product_product_2").id,
                            "quantity": 1.0,
                            "price_unit": 1000,
                            "account_id": cls.account_revenue.id,
                            "tax_ids": False,
                        },
                    )
                ],
            }
        )

        cls.vendor_bill_1 = cls.env["account.move"].create(
            {
                "name": "Test Vendor Invoice 1",
                "move_type": "in_invoice",
                "invoice_date": datetime.now(),
                "journal_id": cls.purchase_journal.id,
                "partner_id": cls.vendor.id,
                "invoice_payment_term_id": cls.payment_term.id,
                "invoice_line_ids": [
                    Command.create(
                        {
                            "product_id": cls.env.ref("product.product_product_3").id,
                            "quantity": 1.0,
                            "price_unit": 500,
                            "account_id": cls.account_expense.id,
                            "tax_ids": False,
                        },
                    )
                ],
            }
        )

        cls.vendor_bill_2 = cls.env["account.move"].create(
            {
                "name": "Test Vendor Invoice 2",
                "move_type": "in_invoice",
                "invoice_date": datetime.now(),
                "journal_id": cls.purchase_journal.id,
                "partner_id": cls.vendor.id,
                "invoice_payment_term_id": cls.payment_term.id,
                "invoice_line_ids": [
                    Command.create(
                        {
                            "product_id": cls.env.ref("product.product_product_2").id,
                            "quantity": 1.0,
                            "price_unit": 200,
                            "account_id": cls.account_expense.id,
                            "tax_ids": False,
                        },
                    )
                ],
            }
        )

    def test_customer_payments_discount(self):
        self.cust_invoice_1.action_post()
        # discount_date should be 10 days(define discount days in payment term)
        # from invoice date
        self.assertEqual(
            self.cust_invoice_1.discount_date,
            self.cust_invoice_1.invoice_date + timedelta(10),
        )
        # check discount amount
        self.assertEqual(self.cust_invoice_1.discount_amt, 10)

        self.cust_invoice_2.action_post()
        # discount_date should be 10 days(define discount days in payment term)
        # from invoice date
        self.assertEqual(
            self.cust_invoice_2.discount_date,
            self.cust_invoice_2.invoice_date + timedelta(10),
        )
        # check discount amount
        self.assertEqual(self.cust_invoice_2.discount_amt, 100)

        context = {
            "active_model": "account.move",
            "batch": True,
            "active_ids": [self.cust_invoice_1.id, self.cust_invoice_2.id],
        }
        with Form(
            self.env["account.payment.register"].with_context(**context)
        ) as register_wizard_form:
            register_wizard = register_wizard_form.save()

        self.assertEqual(
            register_wizard.total_amount,
            self.cust_invoice_1.amount_total
            - self.cust_invoice_1.discount_amt
            + self.cust_invoice_2.amount_total
            - self.cust_invoice_2.discount_amt,
        )

        for invoice_payment_line in register_wizard.invoice_payments:
            self.assertEqual(
                invoice_payment_line.amount,
                invoice_payment_line.invoice_id.amount_total
                - invoice_payment_line.invoice_id.discount_amt,
            )
        register_wizard.make_payments()

        self.assertEqual(self.cust_invoice_1.payment_state, "paid")
        self.assertEqual(self.cust_invoice_2.payment_state, "paid")

    def test_vendor_payments_discount(self):
        self.vendor_bill_1.action_post()
        # discount_date should be 10 days(define discount days in payment term)
        # from bill date
        self.assertEqual(
            self.vendor_bill_1.discount_date,
            self.vendor_bill_1.invoice_date + timedelta(10),
        )
        # check discount amount
        self.assertEqual(self.vendor_bill_1.discount_amt, 50)

        self.vendor_bill_2.action_post()
        # discount_date should be 10 days(define discount days in payment term)
        # from bill date
        self.assertEqual(
            self.vendor_bill_2.discount_date,
            self.vendor_bill_2.invoice_date + timedelta(10),
        )
        # check discount amount
        self.assertEqual(self.vendor_bill_2.discount_amt, 20)

        context = {
            "active_model": "account.move",
            "batch": True,
            "active_ids": [self.vendor_bill_1.id, self.vendor_bill_2.id],
        }
        with Form(
            self.env["account.payment.register"].with_context(**context)
        ) as register_wizard_form:
            register_wizard = register_wizard_form.save()

        self.assertEqual(
            register_wizard.total_amount,
            self.vendor_bill_1.amount_total
            - self.vendor_bill_1.discount_amt
            + self.vendor_bill_2.amount_total
            - self.vendor_bill_2.discount_amt,
        )

        for invoice_payment_line in register_wizard.invoice_payments:
            self.assertEqual(
                invoice_payment_line.amount,
                invoice_payment_line.invoice_id.amount_total
                - invoice_payment_line.invoice_id.discount_amt,
            )
        register_wizard.make_payments()

        self.assertEqual(self.vendor_bill_1.payment_state, "paid")
        self.assertEqual(self.vendor_bill_2.payment_state, "paid")
