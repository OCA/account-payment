# Copyright 2020 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields
from odoo.exceptions import AccessError
from odoo.tests.common import Form, SavepointCase


class TestSalePaymentMgmt(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestSalePaymentMgmt, cls).setUpClass()
        # sers
        users = cls.env["res.users"].with_context(no_reset_password=True)
        # sale_salesman
        cls.user_sale_salesman = users.create(
            {
                "name": "sale_salesman",
                "login": "sale_salesman",
                "email": "sale_salesman@example.com",
                "groups_id": [
                    (6, 0, [cls.env.ref("sales_team.group_sale_salesman").id])
                ],
            }
        )
        # sale_salesman_all_leads
        cls.user_sale_salesman_all_leads = users.create(
            {
                "name": "sale_salesman_all_leads",
                "login": "sale_salesman_all_leads",
                "email": "sale_salesman_all_leads@example.com",
                "groups_id": [
                    (6, 0, [cls.env.ref("sales_team.group_sale_salesman_all_leads").id])
                ],
            }
        )
        # sale_manager
        cls.user_sale_manager = users.create(
            {
                "name": "sale_manager",
                "login": "sale_manager",
                "email": "sale_manager@example.com",
                "groups_id": [
                    (6, 0, [cls.env.ref("sales_team.group_sale_manager").id])
                ],
            }
        )
        # group_account_invoice
        cls.user_account_invoice = users.create(
            {
                "name": "account_invoice",
                "login": "account_invoice",
                "email": "account_invoice@example.com",
                "groups_id": [
                    (6, 0, [cls.env.ref("account.group_account_invoice").id])
                ],
            }
        )
        # without_groups
        cls.user_without_groups = users.create(
            {
                "name": "without_groups",
                "login": "without_groups",
                "email": "without_groups@example.com",
                "groups_id": False,
            }
        )
        # partner
        cls.res_partner = cls.env["res.partner"].create({"name": "Test customer"})
        # account_payment_method
        cls.account_payment_method = cls.env["account.payment.method"].create(
            {"name": "Test", "code": "test", "payment_type": "inbound", "active": True}
        )
        # account_account
        cls.account_account = cls.env["account.account"].create(
            {
                "name": "Test",
                "code": "test_bank",
                "user_type_id": cls.env.ref("account.data_account_type_revenue").id,
                "company_id": cls.env.ref("base.main_company").id,
            }
        )
        # account_journal
        cls.account_journal = cls.env["account.journal"].create(
            {
                "name": "Test Bank Journal",
                "type": "general",
                "code": "TEST-BANK",
                "inbound_payment_method_ids": [(6, 0, [cls.account_payment_method.id])],
                "default_debit_account_id": cls.account_account.id,
                "default_credit_account_id": cls.account_account.id,
            }
        )
        cls.account_payment_vals = {
            "payment_type": "inbound",
            "partner_type": "customer",
            "partner_id": cls.res_partner.id,
            "amount": 100,
            "payment_date": fields.Date.from_string("2019-01-01"),
            "communication": "payment_test",
            "journal_id": cls.account_journal.id,
            "payment_method_id": cls.account_payment_method.id,
        }
        # account_payment
        cls.account_payment = (
            cls.env["account.payment"]
            .sudo(cls.user_sale_salesman.id)
            .create(cls.account_payment_vals)
        )

    def test_access_user_sale_salesman(self):
        self.assertIn(
            self.account_payment.id,
            self.env["account.payment"]
            .with_user(self.user_sale_salesman)
            .search([])
            .ids,
            "User with group sale_salesman should be able to read payments",
        )

    def test_access_user_sale_salesman_all_leads(self):
        self.assertIn(
            self.account_payment.id,
            self.env["account.payment"]
            .with_user(self.user_sale_salesman_all_leads)
            .search([])
            .ids,
            "User with group sale_salesman_all_leads should be able to read payments",
        )

    def test_access_user_sale_manager(self):
        self.assertIn(
            self.account_payment.id,
            self.env["account.payment"]
            .with_user(self.user_sale_manager)
            .search([])
            .ids,
            "User with group sale_manager should be able to read payments",
        )

    def test_access_user_account_invoice(self):
        self.assertIn(
            self.account_payment.id,
            self.env["account.payment"]
            .with_user(self.user_account_invoice)
            .search([])
            .ids,
            "User with group account_invoice should be able to read payments",
        )

    def test_access_user_without_groups(self):
        with self.assertRaises(AccessError):
            self.account_payment.with_user(self.user_without_groups).read()

    def test_create_user_sale_salesman(self):
        view_id = "account.view_account_payment_form"
        with Form(
            self.env["account.payment"].with_user(self.user_sale_salesman), view=view_id
        ) as f:
            f.partner_id = self.res_partner
            f.amount = self.account_payment_vals["amount"]
            f.communication = "user_sale_salesman"
            f.payment_type = "inbound"

        payment = f.save()
        payment.post()

        self.assertEqual(payment.state, "posted")

    def test_create_user_sale_salesman_all_leads(self):
        view_id = "account.view_account_payment_form"
        with Form(
            self.env["account.payment"].with_user(self.user_sale_salesman_all_leads),
            view=view_id,
        ) as f:
            f.partner_id = self.res_partner
            f.amount = self.account_payment_vals["amount"]
            f.communication = "user_sale_salesman_all_leads"
            f.payment_type = "inbound"

        payment = f.save()
        payment.post()

        self.assertEqual(payment.state, "posted")

    def test_create_user_sale_manager(self):
        view_id = "account.view_account_payment_form"
        with Form(
            self.env["account.payment"].with_user(self.user_sale_manager), view=view_id
        ) as f:
            f.partner_id = self.res_partner
            f.amount = self.account_payment_vals["amount"]
            f.communication = "user_sale_manager"
            f.payment_type = "inbound"

        payment = f.save()
        payment.post()

        self.assertEqual(payment.state, "posted")

    def test_create_user_account_invoice(self):
        view_id = "account.view_account_payment_form"
        with Form(
            self.env["account.payment"].with_user(self.user_account_invoice),
            view=view_id,
        ) as f:
            f.partner_id = self.res_partner
            f.amount = self.account_payment_vals["amount"]
            f.communication = "user_account_invoice"
            f.payment_type = "inbound"

        payment = f.save()
        payment.post()

        self.assertEqual(payment.state, "posted")

    def test_user_without_groups(self):
        view_id = "account.view_account_payment_form"
        with self.assertRaises(AccessError):
            with Form(
                self.env["account.payment"].with_user(self.user_without_groups),
                view=view_id,
            ) as f:
                f.partner_id = self.res_partner
                f.amount = self.account_payment_vals["amount"]
                f.communication = "user_without_groups"
                f.payment_type = "inbound"

            payment = f.save()
            payment.post()
