# Copyright 2025 Juan Carlos Oñate - Tecnativa <juancarlos.onate@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from unittest.mock import MagicMock

from odoo.fields import Command

from odoo.addons.payment.tests.common import PaymentCommon


class SequraCommon(PaymentCommon):
    SEQURA_ORDER_ID = "SQ-TEST-ORDER-123"
    SEQURA_SANDBOX_URL = "https://sandbox.sequrapi.com"
    SEQURA_CART_ORDER_ID = "CART-XYZ-789"
    SEQURA_INVOICE_ORDER_ID = "INV-2025-001-SEQURA"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.provider = cls._prepare_provider(
            "sequra",
            update_values={
                "sequra_merchant_id": "MERCHANT-TEST-001",
            },
        )
        cls.reference = "SO123-SETEST"
        cls.amount = 199.99
        cls.currency = cls.env.ref("base.EUR")
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "consu",
                "list_price": 100.0,
            }
        )
        cls.redirect_notification_data = {
            "order_ref_1": cls.reference,
            "sq_state": "approved",
        }
        cls.webhook_notification_data = {
            "order_ref_1": cls.reference,
            "state": "confirmed",
        }
        cls.verification_data = {
            "status_code": 200,
            "text": "OK",
        }
        cls.verification_data_error = {
            "status_code": 500,
            "text": "Error",
        }

    def _create_simple_sale_order(self, quantity=1, price_unit=75.0):
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": quantity,
                            "price_unit": price_unit,
                        }
                    )
                ],
            }
        )
        sale_order.action_confirm()
        return sale_order

    def _create_simple_invoice(self, lines_data=None):
        if lines_data is None:
            lines_data = [{"quantity": 1, "price_unit": 100.0}]
        invoice_lines = []
        for line_data in lines_data:
            invoice_lines.append(
                Command.create(
                    {
                        "product_id": self.product.id,
                        "quantity": line_data["quantity"],
                        "price_unit": line_data["price_unit"],
                    }
                )
            )
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "invoice_line_ids": invoice_lines,
            }
        )
        invoice.action_post()
        return invoice

    def _create_mock_sequra_order_response(self, order_id=None):
        order_id = order_id or self.SEQURA_CART_ORDER_ID
        mock_response = MagicMock()
        mock_response.headers = {
            "Location": f"{self.SEQURA_SANDBOX_URL}/orders/{order_id}"
        }
        return mock_response

    def _create_mock_sequra_update_response(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.text = "OK"
        return mock_response

    def _create_sequra_notification_data(self, order_ref, state="approved"):
        return {
            "order_ref": order_ref,
            "sq_state": state,
        }
