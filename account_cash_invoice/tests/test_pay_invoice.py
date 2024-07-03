# Copyright 2017-2021 Creu Blanca <https://creublanca.es/>
# Copyright (C) 2024 Tecnativa <https://tecnativa.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo.tests import tagged
from odoo.tests.common import Form

from odoo.addons.base.tests.common import BaseCommon


@tagged("post_install", "-at_install")
class TestSessionPayInvoice(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.AccountMove = cls.env["account.move"]
        cls.company = cls.env.ref("base.main_company")
        partner = cls.env.ref("base.partner_demo")
        cls.product = cls.env.ref("product.product_delivery_02")
        account = cls.env["account.account"].create(
            {
                "code": "449000",
                "company_id": cls.company.id,
                "name": "Test",
                "account_type": "income",
                "reconcile": True,
            }
        )
        cls.invoice_out = cls.AccountMove.create(
            {
                "company_id": cls.company.id,
                "partner_id": partner.id,
                "date": "2016-03-12",
                "move_type": "out_invoice",
                "invoice_line_ids": [
                    (
                        0,
                        False,
                        {
                            "product_id": cls.product.id,
                            "account_id": account.id,
                            "name": "Producto de prueba",
                            "quantity": 1.0,
                            "price_unit": 100.0,
                            "tax_ids": [],
                        },
                    )
                ],
            }
        )
        cls.invoice_out.action_post()
        cls.invoice_out.name = "2999/99999"
        cls.invoice_in = cls.AccountMove.create(
            {
                "partner_id": partner.id,
                "company_id": cls.company.id,
                "move_type": "in_invoice",
                "date": "2016-03-12",
                "invoice_date": "2016-03-12",
                "invoice_line_ids": [
                    (
                        0,
                        False,
                        {
                            "product_id": cls.product.id,
                            "name": "Producto de prueba",
                            "account_id": account.id,
                            "quantity": 1.0,
                            "price_unit": 100.0,
                            "tax_ids": [],
                        },
                    )
                ],
            }
        )
        cls.invoice_in.action_post()
        cls.invoice_in.name = "2999/99999"
        cls.journal = (
            cls.env["account.journal"]
            .search(
                [("company_id", "=", cls.company.id), ("type", "=", "cash")], limit=1
            )
            .ensure_one()
        )

    def test_bank_statement(self):
        invoice_in_obj = self.env["cash.pay.invoice"].with_context(
            active_ids=self.journal.ids, active_model=self.journal._name
        )
        with Form(invoice_in_obj) as in_invoice:
            in_invoice.invoice_type = "vendor"
            in_invoice.invoice_id = self.invoice_in
            self.assertEqual(-100, in_invoice.amount)
            self.assertEqual(in_invoice.journal_id, self.journal)
        invoice_in_obj.browse(in_invoice.id).action_pay_invoice()

        invoice_out_obj = self.env["cash.pay.invoice"].with_context(
            active_ids=self.journal.ids, active_model=self.journal._name
        )
        with Form(invoice_out_obj) as out_invoice:
            out_invoice.invoice_type = "customer"
            out_invoice.invoice_id = self.invoice_out
            self.assertEqual(100, out_invoice.amount)
            self.assertEqual(in_invoice.journal_id, self.journal)
        invoice_out_obj.browse(out_invoice.id).action_pay_invoice()
        inv_lines = self.invoice_in.line_ids.filtered(
            lambda line: line.account_id.account_type
            in ("asset_receivable", "liability_payable")
        )
        inv_lines |= self.invoice_out.line_ids.filtered(
            lambda line: line.account_id.account_type
            in ("asset_receivable", "liability_payable")
        )
        self.assertEqual(self.invoice_out.amount_residual, 0.0)
        self.assertEqual(self.invoice_in.amount_residual, 0.0)
