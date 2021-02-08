# Copyright 2017 Creu Blanca <https://creublanca.es/>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo.tests.common import SavepointCase


class TestSessionPayInvoice(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.ref("base.main_company")
        partner = cls.env.ref("base.partner_demo")
        cls.product = cls.env.ref("product.product_delivery_02")
        account = cls.env["account.account"].create(
            {
                "code": "test_cash_pay_invoice",
                "company_id": cls.company.id,
                "name": "Test",
                "user_type_id": cls.env.ref("account.data_account_type_revenue").id,
                "reconcile": True,
            }
        )
        cls.invoice_out = cls.env["account.move"].create(
            {
                "company_id": cls.company.id,
                "partner_id": partner.id,
                "date": "2016-03-12",
                "type": "out_invoice",
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
                        },
                    )
                ],
            }
        )
        cls.invoice_out._onchange_invoice_line_ids()
        cls.invoice_out.action_post()
        cls.invoice_out.name = "2999/99999"
        cls.invoice_in = cls.env["account.move"].create(
            {
                "partner_id": partner.id,
                "company_id": cls.company.id,
                "type": "in_invoice",
                "date": "2016-03-12",
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
                        },
                    )
                ],
            }
        )
        cls.invoice_in._onchange_invoice_line_ids()
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
        statement = self.env["account.bank.statement"].create(
            {"name": "Statement", "journal_id": self.journal.id}
        )
        in_invoice = (
            self.env["cash.invoice.in"]
            .with_context(active_ids=statement.ids, active_model=statement._name)
            .create({"invoice_id": self.invoice_in.id, "amount": 100.0})
        )
        in_invoice.run()
        in_invoice.compute_journal_count()
        self.assertEqual(in_invoice.journal_count, 1)
        out_invoice = (
            self.env["cash.invoice.out"]
            .with_context(active_ids=statement.ids, active_model=statement._name)
            .create({"invoice_id": self.invoice_out.id, "amount": 100.0})
        )
        out_invoice.run()
        statement.balance_end_real = statement.balance_start
        action = statement.check_confirm_bank()
        if action:
            self.env[action.get("res_model")].with_context(
                active_id=statement.id,
                active_ids=statement.ids,
                active_model=statement._name,
            ).validate()
        self.assertEqual(self.invoice_out.amount_residual, 0.0)
        self.invoice_in.invalidate_cache()
        self.assertEqual(self.invoice_in.amount_residual, 0.0)
        out_invoice.compute_journal_count()
        self.assertEqual(out_invoice.journal_count, 1)
