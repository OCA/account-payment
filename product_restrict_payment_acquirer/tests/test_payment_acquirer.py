from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPaymentAcquirer(TransactionCase):
    def setUp(self) -> None:
        super(TestPaymentAcquirer, self).setUp()

        # Setup acquirers
        self.paypal = self.env.ref("payment.payment_acquirer_paypal")
        self.paypal.write({"state": "test"})
        self.acquirers = self.env["payment.acquirer"].search(
            [("state", "in", ["enabled", "test"])]
        )
        self.wire_transfer = self.env.ref("payment.payment_acquirer_transfer")

        # Setup partner
        self.res_partner_deco = self.env.ref("base.res_partner_2")
        self.res_partner_deco.write(
            {"allowed_acquirer_ids": [(4, self.wire_transfer.id)]}
        )

        # Setup order
        self.product_1 = self.env["product.product"].create(
            {
                "name": "Test Product 1",
                "allowed_product_acquirer_ids": [
                    (4, self.wire_transfer.id),
                    (4, self.paypal.id),
                ],
            }
        )
        self.product_2 = self.env["product.product"].create(
            {
                "name": "Test Product 2",
                "allowed_product_acquirer_ids": [(4, self.paypal.id)],
            }
        )
        self.order = self.env["sale.order"].create(
            {
                "partner_id": self.res_partner_deco.id,
                "order_line": [
                    (0, 0, {"product_id": self.product_1.id, "product_uom_qty": 1.0}),
                    (0, 0, {"product_id": self.product_2.id, "product_uom_qty": 1.0}),
                ],
            }
        )

    def test_get_allowed_acquirers_blank_option(self):
        """This test covers acquirer restriction mode settings set to blank option
        fall back to partner acquirers behaviour"""
        self.env["ir.config_parameter"].set_param(
            "product_acquirer_settings.product_acquirer_restriction_mode", False
        )
        all_acquirers = list(self.acquirers)
        result = self.env["payment.acquirer"].get_allowed_acquirers(
            all_acquirers, order_id=self.order.id
        )
        self.assertListEqual(
            result,
            [self.wire_transfer],
            msg="The acquirer must be same as assigned to the partner (Wire transfer)",
        )

        # If there's no order
        result = self.env["payment.acquirer"].get_allowed_acquirers(
            all_acquirers, order_id=None
        )
        self.assertListEqual(
            result,
            [self.wire_transfer, self.paypal],
            msg="All enabled acquirers must be returned",
        )

    def test_get_allowed_acquirers_first_option(self):
        """This test covers acquirer restriction mode settings set to the "first" option
        and recalls acquirers set for the product in first sale order line"""
        self.env["ir.config_parameter"].set_param(
            "product_acquirer_settings.product_acquirer_restriction_mode", "first"
        )
        all_acquirers = list(self.acquirers)
        result = self.env["payment.acquirer"].get_allowed_acquirers(
            all_acquirers, order_id=self.order.id
        )
        self.assertListEqual(
            result,
            [self.wire_transfer, self.paypal],
            msg="Must be two acquirers as assigned to the product in first order line",
        )

        # If there's no order
        result = self.env["payment.acquirer"].get_allowed_acquirers(
            all_acquirers, order_id=None
        )
        self.assertListEqual(
            result,
            [self.wire_transfer, self.paypal],
            msg="All enabled acquirers must be returned",
        )

    def test_get_allowed_acquirers_all_option(self):
        """This test covers acquirer restriction mode settings set to the "all" option
        and recalls common acquirer for all products in the sale order"""
        self.env["ir.config_parameter"].set_param(
            "product_acquirer_settings.product_acquirer_restriction_mode", "all"
        )
        all_acquirers = list(self.acquirers)
        result = self.env["payment.acquirer"].get_allowed_acquirers(
            all_acquirers, order_id=self.order.id
        )
        self.assertListEqual(
            result,
            [self.paypal],
            msg="The acquirer must equal common line for both order lines (Paypal)",
        )

        # If there's no order
        result = self.env["payment.acquirer"].get_allowed_acquirers(
            all_acquirers, order_id=None
        )
        self.assertListEqual(
            result,
            [self.wire_transfer, self.paypal],
            msg="All enabled acquirers must be returned",
        )
