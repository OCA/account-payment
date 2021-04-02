# Copyright 2019 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime, timedelta

# from odoo import fields
from odoo.tests import common
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class TestPaymentCreditCard(common.TransactionCase):
    def setUp(self):
        super(TestPaymentCreditCard, self).setUp()
        self.account_invoice_obj = self.env["account.move"]
        self.account_move_line_obj = self.env["account.move.line"]
        self.account_account_obj = self.env["account.account"]
        self.account_journal_obj = self.env["account.journal"]
        self.account_receivable = self.env.ref("account.data_account_type_receivable")
        self.partner_12 = self.env.ref("base.res_partner_12")

        self.journal_sale = self.account_journal_obj.create(
            {"name": "sale_0", "code": "SALE0", "type": "sale", "credit_card": True}
        )
        self.account_id = self.account_account_obj.create(
            {
                "code": "RA1000",
                "name": "Test Receivable Account",
                "user_type_id": self.account_receivable.id,
                "reconcile": True,
            }
        )

        self.invoice_data_list = [
            # Customer Invoice Data
            [
                "out_invoice",
                self.get_date(set_days=30),
                self.partner_12.id,
                self.journal_sale.id,
            ],
        ]

    def test_create_invoice_with_cc(self):
        for invoice_data in self.invoice_data_list:
            invoice = self.account_invoice_obj.with_context(
                default_journal_id=invoice_data[3]
            ).create(
                {
                    "ref": "reference",
                    "move_type": invoice_data[0],
                    "invoice_date": invoice_data[1],
                    "invoice_date_due": invoice_data[1],
                    "partner_id": invoice_data[2],
                }
            )
            self.account_move_line_obj.create(
                {
                    "product_id": self.env.ref("product.product_product_4").id,
                    "quantity": 1.0,
                    "price_unit": 0,
                    "move_id": invoice.id,
                    "name": "product that cost 100",
                    "account_id": self.account_id.id,
                }
            )
            invoice._post(soft=False)
            return invoice

    def get_date(self, set_days):
        return (datetime.now() - timedelta(days=-set_days)).strftime(
            DEFAULT_SERVER_DATE_FORMAT
        )
