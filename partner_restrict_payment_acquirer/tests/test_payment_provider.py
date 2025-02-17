from odoo.fields import Command
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPaymentProvider(TransactionCase):
    def setUp(self):
        """
        Set up required records for testing payment provider compatibility
        """
        super().setUp()

        # Create a test partner
        self.partner = self.env["res.partner"].create({"name": "Test Partner"})
        # Create a test product
        self.product = self.env["product.product"].create(
            {
                "name": "Test Product",
            }
        )
        # Create a test sale order
        self.sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": self.product.name,
                            "product_id": self.product.id,
                            "product_uom_qty": 1,
                            "price_unit": 10,
                        },
                    ),
                ],
            }
        )
        # Create a dummy provider to allow basic tests without any
        # specific provider implementation
        arch = """
        <form action="dummy" method="post">
            <input type="hidden" name="view_id" t-att-value="viewid"/>
            <input type="hidden" name="user_id" t-att-value="user_id.id"/>
        </form>
        """
        # We exploit the default values `viewid` and `user_id`
        # from QWeb's rendering context
        redirect_form = self.env["ir.ui.view"].create(
            {
                "name": "Dummy Redirect Form",
                "type": "qweb",
                "arch": arch,
            }
        )
        self.dummy_provider = self.env["payment.provider"].create(
            {
                "name": "Dummy Provider",
                "code": "none",
                "state": "test",
                "is_published": True,
                "payment_method_ids": [
                    Command.set([self.env.ref("payment.payment_method_unknown").id])
                ],
                "allow_tokenization": True,
                "redirect_form_view_id": redirect_form.id,
            }
        )
        # Activate pm
        self.env.ref("payment.payment_method_unknown").write(
            {
                "active": True,
                "support_tokenization": True,
            }
        )
        # Activate wire transfer provider
        self.wire_transfer = self.env.ref("payment.payment_provider_transfer")
        self.wire_transfer.write({"state": "test", "is_published": True})
        # Fetch all active providers
        self.providers = self.env["payment.provider"].search(
            [("state", "in", ["enabled", "test"])]
        )

    def test_partner_compatible_providers(self):
        """
        Test fetching compatible payment providers for a partner
        """
        compatible_providers = (
            self.env["payment.provider"]
            .sudo()
            ._get_compatible_providers(
                self.sale_order.company_id.id,
                self.partner.id,
                self.sale_order.amount_total,
                sale_order_id=self.sale_order.id,
            )
        )
        self.assertEqual(
            self.providers,
            compatible_providers,
            "Initially, all test providers should be available",
        )

        # Restrict partner to only wire transfer provider
        self.partner.allowed_payment_provider_ids = self.wire_transfer.ids
        compatible_providers = (
            self.env["payment.provider"]
            .sudo()
            ._get_compatible_providers(
                self.sale_order.company_id.id,
                self.partner.id,
                self.sale_order.amount_total,
                sale_order_id=self.sale_order.id,
            )
        )
        self.assertEqual(
            len(compatible_providers),
            1,
            "After restriction, only one provider should be available",
        )
        self.assertNotEqual(
            self.providers,
            compatible_providers,
            "Restricted providers list should differ from the original set",
        )
