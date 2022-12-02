# Copyright 2022 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import common


class TestProjectPropagation(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.partner = cls.env["res.partner"].create({"name": "Partner #1"})
        cls.product = cls.env["product.product"].create({"name": "Product Test"})
        cls.payment_term = cls.env.ref(
            "account.account_payment_term_end_following_month"
        )
        cls.precision = cls.env["decimal.precision"].precision_get("Product Price")

    def test_cash_discount_base_sale(self):

        payment_term = self.payment_term
        payment_term.discount_percent = 5
        payment_term.discount_delay = 5

        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "payment_term_id": self.payment_term.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 1,
                            "name": self.product.name,
                            "price_unit": 100,
                            "tax_id": False,
                        },
                    )
                ],
            }
        )
        sale_order.with_context().action_confirm()
        sale_order.with_context()._create_invoices()

        account_move_line = self.env["account.move.line"].search(
            [("product_id", "=", self.product.id)]
        )
        self.assertTrue(account_move_line)

        self.assertEqual(
            account_move_line.move_id.discount_percent, payment_term.discount_percent
        )
        self.assertEqual(
            account_move_line.move_id.discount_delay, payment_term.discount_delay
        )
        # Ensures that discount_amount is set correctly
        self.assertAlmostEqual(
            account_move_line.move_id.discount_amount, 5, self.precision
        )
