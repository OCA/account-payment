# Copyright 2018 Open Source Integrators (http://www.opensourceintegrators.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.tests import common


class TestPaymentTermDiscount(common.TransactionCase):
    def setUp(self):
        super().setUp()

        # Refs
        self.main_company = self.env.ref("base.main_company")
        self.partner_id = self.env.ref("base.res_partner_4")
        self.journalrec = self.env["account.journal"].search([("type", "=", "sale")])[0]
        res_users_account_manager = self.env.ref("account.group_account_manager")
        partner_manager = self.env.ref("base.group_partner_manager")
        account_user_type_expenses = self.env.ref("account.data_account_type_expenses")
        account_user_type_receivable = self.env.ref(
            "account.data_account_type_receivable"
        )
        self.payment_method = self.env.ref("account.account_payment_method_manual_in")

        # Get required Model
        self.account_invoice_model = self.env["account.move"]
        self.account_model = self.env["account.account"]
        self.payment_term_model = self.env["account.payment.term"]
        self.user_model = self.env["res.users"]
        self.payment_model = self.env["account.payment"]

        # Create users
        self.account_manager = self.user_model.with_context(
            {"no_reset_password": True}
        ).create(
            dict(
                name="Adviser",
                company_id=self.main_company.id,
                login="fm_adviser",
                email="accountmanager@yourcompany.com",
                groups_id=[(6, 0, [res_users_account_manager.id, partner_manager.id])],
            )
        )

        # Create expense account for discount
        self.account_discount_id = self.account_model.with_user(
            self.account_manager.id
        ).create(
            dict(
                code="cust_acc_discount",
                name="Discount Expenses",
                user_type_id=account_user_type_expenses.id,
                reconcile=True,
            )
        )

        # Income account
        self.income_account = self.account_model.with_user(
            self.account_manager.id
        ).search(
            [
                (
                    "user_type_id",
                    "=",
                    self.env.ref("account.data_account_type_revenue").id,
                )
            ],
            limit=1,
        )

        # Create receivable account
        self.account_rec1_id = self.account_model.with_user(
            self.account_manager.id
        ).create(
            dict(
                code="cust_acc_rec",
                name="Customer invoice receivable",
                user_type_id=account_user_type_receivable.id,
                reconcile=True,
            )
        )

        # Create Payment term
        self.payment_term = self.payment_term_model.with_user(
            self.account_manager.id
        ).create(
            dict(
                name="5%10 NET30",
                is_discount=True,
                note="5% discount if payment done within 10 days, otherwise net",
                line_ids=[
                    (
                        0,
                        0,
                        {
                            "value": "balance",
                            "discount": 5.0,
                            "discount_days": 10,
                            "discount_expense_account_id": self.account_discount_id.id,
                            "days": 30,
                        },
                    )
                ],
            )
        )

        # Create customer invoice
        self.customer_invoice = self.account_invoice_model.with_user(
            self.account_manager.id
        ).create(
            dict(
                name="Test Customer Invoice",
                move_type="out_invoice",
                invoice_date=fields.Date.today(),
                invoice_payment_term_id=self.payment_term.id,
                journal_id=self.journalrec.id,
                partner_id=self.partner_id.id,
            )
        )
        # Prepare invoice line values
        self.customer_invoice.write(
            {
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.env.ref("product.product_product_5").id,
                            "quantity": 10.0,
                            "account_id": self.income_account.id,
                            "name": "product test 5",
                            "price_unit": 100.00,
                        },
                    )
                ]
            }
        )
        # Validate customer invoice
        self.customer_invoice.action_post()

    def _do_payment(self, invoice, amount, date):
        """
        Create Payment wizard helper function
        """
        ctx = {
            "active_ids": [invoice.id],
            "active_id": invoice.id,
            "active_model": "account.move",
        }
        PaymentWizard = self.env["account.payment.register"]
        view = "account.view_account_payment_register_form"
        with common.Form(PaymentWizard.with_context(ctx), view=view) as f:
            f.amount = amount
            f.payment_date = date
        payment = f.save()
        return payment.action_create_payments()

    def test_customer_invoice_payment_term_discount(self):
        """Test customer invoice and payment term discount"""
        # Update payment date that's match with condition within 10 days
        payment_date = self.customer_invoice.invoice_date + relativedelta(days=9)
        self._do_payment(self.customer_invoice, 950.0, payment_date)
        # Verify that invoice is now in Paid state
        self.assertEqual(self.customer_invoice.payment_state, "paid")

    def test_customer_invoice_payment_term_no_discount(self):
        """ Create customer invoice and verify workflow without discount """
        # Update payment date that does not match with condition within 10 days
        payment_date = self.customer_invoice.invoice_date + relativedelta(days=15)
        self._do_payment(self.customer_invoice, 950.0, payment_date)
        # Verify that invoice is now in Partial state
        self.assertEqual(self.customer_invoice.payment_state, "paid")
