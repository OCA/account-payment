# Copyright 2025 Cetmix
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.fields import Command
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPaymentProvider(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})
        cls.product = cls.env["product.product"].create({"name": "Test Product"})
        cls.sale_order = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner.id,
                "order_line": [
                    Command.create(
                        {
                            "name": cls.product.name,
                            "product_id": cls.product.id,
                            "product_uom_qty": 1,
                            "price_unit": 10,
                        }
                    ),
                ],
            }
        )

        # A provider of our own, so the test does not depend on which ones a
        # database happens to carry.
        arch = """
        <form action="dummy" method="post">
            <input type="hidden" name="view_id" t-att-value="viewid"/>
            <input type="hidden" name="user_id" t-att-value="user_id.id"/>
        </form>
        """
        redirect_form = cls.env["ir.ui.view"].create(
            {"name": "Dummy Redirect Form", "type": "qweb", "arch": arch}
        )
        cls.dummy_provider = cls.env["payment.provider"].create(
            {
                "name": "Dummy Provider",
                "code": "none",
                "state": "test",
                "is_published": True,
                "payment_method_ids": [
                    Command.set([cls.env.ref("payment.payment_method_unknown").id])
                ],
                "allow_tokenization": True,
                "redirect_form_view_id": redirect_form.id,
            }
        )
        # After the provider, not before: 19.0 refuses to activate a payment
        # method until a provider that supports it is enabled.
        cls.env.ref("payment.payment_method_unknown").write(
            {"active": True, "support_tokenization": True}
        )
        cls.wire_transfer = cls.env.ref("payment.payment_provider_transfer")
        cls.wire_transfer.write({"state": "test", "is_published": True})

    def _compatible(self, partner=None):
        """The providers Odoo would offer for this order, as the payment form asks."""
        return (
            self.env["payment.provider"]
            .sudo()
            ._get_compatible_providers(
                self.sale_order.company_id.id,
                (partner or self.partner).id,
                self.sale_order.amount_total,
                sale_order_id=self.sale_order.id,
            )
        )

    def test_an_unrestricted_partner_is_offered_everything_compatible(self):
        """The baseline is what Odoo offers, not every provider that exists.

        A real database carries providers excluded for their own reasons - a
        country list, a currency, a custom mode - so comparing against "every
        provider in state enabled or test" fails for reasons that have nothing
        to do with this module.
        """
        offered = self._compatible()
        self.assertIn(self.dummy_provider, offered)
        self.assertIn(self.wire_transfer, offered)

    def test_a_restriction_narrows_the_offer_to_exactly_the_allowed_ones(self):
        self.partner.allowed_payment_provider_ids = self.wire_transfer
        self.assertEqual(self._compatible(), self.wire_transfer)

    def test_an_allowed_provider_that_is_not_compatible_is_still_not_offered(self):
        """The restriction narrows the offer; it never widens it."""
        self.dummy_provider.state = "disabled"
        self.partner.allowed_payment_provider_ids = (
            self.wire_transfer | self.dummy_provider
        )
        self.assertEqual(self._compatible(), self.wire_transfer)

    def test_an_empty_restriction_restricts_nothing(self):
        unrestricted = self._compatible()
        self.partner.allowed_payment_provider_ids = self.wire_transfer
        self.partner.allowed_payment_provider_ids = False
        self.assertEqual(self._compatible(), unrestricted)

    def test_the_restriction_follows_the_partner_being_paid_for(self):
        """Not the logged-in user - which is what makes this work on eCommerce.

        On 15.0 the website checkout had to be handled by a second module,
        because its acquirer lookup read the logged-in user's partner rather
        than taking one. Since 17.0 there is a single funnel,
        `_get_compatible_providers(company_id, partner_id, amount, ...)`, and
        `website_sale`'s checkout controller subclasses the very
        `payment.PaymentPortal` that calls it. So restricting a partner who is
        not the current user still takes effect, and the eCommerce extension
        that 15.0 needed has nothing left to do here.
        """
        other = self.env["res.partner"].create({"name": "Somebody Else"})
        self.partner.allowed_payment_provider_ids = self.wire_transfer
        self.assertEqual(self._compatible(), self.wire_transfer)
        self.assertIn(self.dummy_provider, self._compatible(partner=other))
        self.assertNotEqual(self.env.user.partner_id, self.partner)
