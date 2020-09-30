# Copyright 2016 ForgeFlow S.L.
#   (<http://www.forgeflow.com>).
# Copyright 2016 Therp BV (<http://therp.nl>).
# Copyright 2016 Serpent Consulting Services Pvt. Ltd.
#   (<http://www.serpentcs.com>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from datetime import date, timedelta

from odoo import exceptions, fields
from odoo.tests.common import TransactionCase


class TestAccountDueListDaysOverdue(TransactionCase):
    def setUp(self):
        super(TestAccountDueListDaysOverdue, self).setUp()
        self.overdue_term_model = self.env["account.overdue.term"]
        self.account_user_type = self.env.ref("account.data_account_type_receivable")
        self.revenue_user_type = self.env.ref("account.data_account_type_revenue")
        self.account = self.env["account.account"]
        self.account_move_model = self.env["account.move"]
        self.account_move_line_model = self.env["account.move.line"]
        self.account_journal_model = self.env["account.journal"]
        self.overdue_term_1 = self.env.ref(
            "account_due_list_days_overdue.overdue_term_1"
        )
        self.partner_agrolait = self.env.ref("base.res_partner_1")
        self.currency_usd = self.env.ref("base.USD")
        self.payment_term = self.env.ref("account.account_payment_term_15days")
        self.product = self.env.ref("product.product_product_4")
        self.company = self.env.ref("base.main_company")
        self._create_account_type()
        self.sale_journal = self.account_journal_model.create(
            {
                "name": "Company Sale journal",
                "type": "sale",
                "code": "SALE",
                "company_id": self.company.id,
            }
        )
        # we create an invoice
        inv_date = date.today() - timedelta(days=16)
        inv_data = {
            "name": "invoice to customer",
            "partner_id": self.partner_agrolait.id,
            "currency_id": self.currency_usd.id,
            "invoice_date": fields.Date.to_string(inv_date),
            "journal_id": self.sale_journal.id,
            "type": "out_invoice",
            "invoice_payment_term_id": self.payment_term.id,
            "invoice_line_ids": [],
        }
        line_data = {
            "product_id": self.product.id,
            "name": "product that cost 100",
            "account_id": self.sales_account.id,
            "price_unit": 100,
            "quantity": 1,
        }
        inv_data["invoice_line_ids"].append((0, 0, line_data))
        self.invoice = self.account_move_model.create(inv_data)
        self.invoice.post()

    def _create_account_type(self):
        # Create receivable and sales test account
        self.receivable_account = self.account.create(
            {
                "name": "Recv - Test",
                "code": "test_recv",
                "user_type_id": self.account_user_type.id,
                "company_id": self.company.id,
                "reconcile": True,
            }
        )
        self.sales_account = self.account.create(
            {
                "name": "Local Sales - Test",
                "code": "test_sales",
                "user_type_id": self.revenue_user_type.id,
                "company_id": self.company.id,
            }
        )

    def test_workflow_open(self):
        self.assertEqual(self.invoice.state, "posted")

    def test_due_days(self):
        for line in self.invoice.line_ids:
            if line.account_id == self.receivable_account:
                self.assertEqual(
                    line.days_overdue,
                    1,
                    "Incorrect calculation of number of days " "overdue",
                )

    def test_overdue_term(self):
        self.account_move_line_model._register_hook()
        for line in self.invoice.line_ids:
            if line.account_id == self.receivable_account:
                self.assertEqual(
                    line[self.overdue_term_1.tech_name],
                    line.amount_residual,
                    "Overdue term 1-30 should contain a due amount",
                )

    def test_ovelapping_overdue_term(self):
        with self.assertRaises(exceptions.ValidationError):
            self.overdue_term_test = self.overdue_term_model.create(
                {"name": "25-30", "from_day": 25, "to_day": 30}
            )
