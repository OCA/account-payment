# Copyright 2012 Open Source Integrators
# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime, timedelta

from odoo import fields
from odoo.tests import common
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class TestPartnerAging(common.TransactionCase):
    def setUp(self):
        super(TestPartnerAging, self).setUp()
        self.partner_aging_date_model = self.env["res.partner.aging.date"]
        self.partner_aging_supplier_model = self.env["res.partner.aging.supplier"]
        self.partner_aging_customer_model = self.env["res.partner.aging.customer"]
        self.current_date = fields.Date.today()
        self.account_invoice_obj = self.env["account.move"]
        self.account_move_line_obj = self.env["account.move.line"]
        self.account_account_obj = self.env["account.account"]
        self.account_journal_obj = self.env["account.journal"]

        self.account_receivable = self.env.ref("account.data_account_type_receivable")
        self.partner_12 = self.env.ref("base.res_partner_12")
        self.partner_2 = self.env.ref("base.res_partner_2")
        self.partner_10 = self.env.ref("base.res_partner_10")
        self.partner_3 = self.env.ref("base.res_partner_3")
        self.partner_18 = self.env.ref("base.res_partner_18")

        self.journal_sale = self.account_journal_obj.create(
            {"name": "sale_0", "code": "SALE0", "type": "sale"}
        )
        self.journal_purchase = self.account_journal_obj.create(
            {"name": "purchase_0", "code": "PRCHASE0", "type": "purchase"}
        )

        self.account_id = self.account_account_obj.create(
            {
                "code": "RA1000",
                "name": "Test Receivable Account",
                "user_type_id": self.account_receivable.id,
                "reconcile": True,
            }
        )

        invoice_data_list = [
            # Customer Invoice Data
            [
                "out_invoice",
                self.get_date(30),
                self.partner_12.id,
                self.journal_sale.id,
            ],
            ["out_invoice", self.get_date(60), self.partner_2.id, self.journal_sale.id],
            [
                "out_invoice",
                self.get_date(90),
                self.partner_18.id,
                self.journal_sale.id,
            ],
            [
                "out_invoice",
                self.get_date(119),
                self.partner_3.id,
                self.journal_sale.id,
            ],
            [
                "out_invoice",
                self.get_date(124),
                self.partner_10.id,
                self.journal_sale.id,
            ],
            # Supplier Invoice Data
            [
                "in_invoice",
                self.get_date(30),
                self.partner_12.id,
                self.journal_purchase.id,
            ],
            [
                "in_invoice",
                self.get_date(60),
                self.partner_2.id,
                self.journal_purchase.id,
            ],
            [
                "in_invoice",
                self.get_date(90),
                self.partner_18.id,
                self.journal_purchase.id,
            ],
            [
                "in_invoice",
                self.get_date(119),
                self.partner_3.id,
                self.journal_purchase.id,
            ],
            [
                "in_invoice",
                self.get_date(124),
                self.partner_10.id,
                self.journal_purchase.id,
            ],
        ]
        for invoice in invoice_data_list:
            self._create_invoice_with_reference(invoice)

    def _create_invoice_with_reference(self, invoice_data):
        invoice = self.account_invoice_obj.with_context(
            default_journal_id=invoice_data[3], test_no_refuse_ref=True
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
        invoice.action_post()
        return invoice

    def get_date(self, set_days):
        return (datetime.now() - timedelta(days=-set_days)).strftime(
            DEFAULT_SERVER_DATE_FORMAT
        )

    def test_partner_aging_customer(self):
        partner_aging_date = self.partner_aging_date_model.create(
            {"age_date": self.current_date}
        )
        res = partner_aging_date.open_customer_aging()
        self.assertEqual(res["context"]["age_date"], self.current_date)
        partner_aging_customer_rec = self.partner_aging_customer_model.search(
            [("invoice_id", "!=", False)], limit=1
        )
        partner_aging_customer_rec.open_document()

    def test_partner_aging_supplier(self):
        partner_aging_date = self.partner_aging_date_model.create(
            {"age_date": self.current_date}
        )
        res = partner_aging_date.open_supplier_aging()
        self.assertEqual(res["context"]["age_date"], self.current_date)
        partner_aging_supplier_rec = self.partner_aging_supplier_model.search(
            [("invoice_id", "!=", False)], limit=1
        )
        partner_aging_supplier_rec.open_document()
