# Copyright 2024 Coop IT Easy SC
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import Command
from odoo.tests.common import Form, TransactionCase


class TestAccountPaymentBatchProcess(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner = cls.env.ref("base.res_partner_12")
        cls.account_receivable = cls.partner.property_account_receivable_id
        cls.sale_journal = cls.env["account.journal"].search(
            [("type", "=", "sale")], limit=1
        )
        cls.account_revenue = cls.env["account.account"].search(
            [
                ("account_type", "=", "income"),
                ("company_id", "=", cls.env.company.id),
            ],
            limit=1,
        )

        cls.cust_invoice_1 = cls.env["account.move"].create(
            {
                "name": "Test Customer Invoice 1",
                "move_type": "out_invoice",
                "journal_id": cls.sale_journal.id,
                "partner_id": cls.partner.id,
                "invoice_line_ids": [
                    Command.create(
                        {
                            "product_id": cls.env.ref("product.product_product_3").id,
                            "quantity": 1.0,
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
                "invoice_line_ids": [
                    Command.create(
                        {
                            "product_id": cls.env.ref("product.product_product_2").id,
                            "quantity": 1.0,
                            "account_id": cls.account_revenue.id,
                            "tax_ids": False,
                        },
                    )
                ],
            }
        )

    def test_auto_fill_payments(self):
        self.cust_invoice_1.action_post()
        self.cust_invoice_2.action_post()

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
            self.cust_invoice_1.amount_total + self.cust_invoice_2.amount_total,
        )

        register_wizard.auto_fill_payments()
        for invoice_payment_line in register_wizard.invoice_payments:
            self.assertEqual(
                invoice_payment_line.amount,
                invoice_payment_line.invoice_id.amount_total,
            )
        register_wizard.make_payments()

        self.assertEqual(self.cust_invoice_1.state, "posted")
        self.assertEqual(self.cust_invoice_2.state, "posted")
