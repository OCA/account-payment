# Copyright 2025 Juan Carlos Oñate - Tecnativa <juancarlos.onate@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from unittest.mock import patch
from urllib.parse import quote as url_quote

from odoo.tests import tagged
from odoo.tools import mute_logger

from odoo.addons.payment.tests.http_common import PaymentHttpCommon
from odoo.addons.payment_sequra.tests.common import SequraCommon


@tagged("post_install", "-at_install")
class TestPaymentTransaction(SequraCommon, PaymentHttpCommon):
    def test_prepare_order_payload_contains_required_fields(self):
        tx = self._create_transaction(flow="redirect")
        request_payload = tx._sequra_prepare_order_request_payload()
        order = request_payload["order"]
        self.assertIn("merchant", order)
        self.assertIn("cart", order)
        self.assertIn("customer", order)
        self.assertIn("delivery_address", order)
        self.assertIn("invoice_address", order)
        self.assertIn("merchant_reference", order)
        self.assertEqual(order["merchant_reference"]["order_ref_1"], tx.reference)

    @mute_logger("odoo.addons.payment_sequra.models.payment_transaction")
    def test_rendering_values_include_checkout_url(self):
        tx = self._create_transaction(flow="redirect")
        with patch(
            "odoo.addons.payment_sequra.models.payment_provider.PaymentProvider._sequra_make_request",
            return_value=self._create_mock_sequra_order_response("ORDER123"),
        ):
            rendering_values = tx._get_specific_rendering_values({})
        self.assertIn("api_url", rendering_values)
        self.assertIn("/embedded_form", rendering_values["api_url"])

    @mute_logger("odoo.addons.payment_sequra.models.payment_transaction")
    def test_process_notification_sets_done(self):
        tx = self._create_transaction(flow="redirect")
        tx.provider_reference = "ORDER123"
        with patch(
            "odoo.addons.payment_sequra.models.payment_provider.PaymentProvider._sequra_make_request",
            return_value=self._create_mock_sequra_update_response(),
        ):
            tx._process_notification_data(self.redirect_notification_data)
        self.assertEqual(tx.state, "done")

    @mute_logger("odoo.addons.payment_sequra.models.payment_transaction")
    def test_process_notification_sets_error_on_failure(self):
        tx = self._create_transaction(flow="redirect")
        tx.provider_reference = "ORDER123"
        mock_error_response = self._create_mock_sequra_update_response()
        mock_error_response.status_code = 500
        mock_error_response.ok = False
        mock_error_response.text = "Server Error"
        mock_error_response.reason = "Internal Server Error"
        with patch(
            "odoo.addons.payment_sequra.models.payment_provider.PaymentProvider._sequra_make_request",
            return_value=mock_error_response,
        ):
            tx._process_notification_data(self.redirect_notification_data)
        self.assertEqual(tx.state, "error")

    @mute_logger("odoo.addons.payment_sequra.models.payment_transaction")
    def test_cancellation_event_cancels_transaction(self):
        tx = self._create_transaction(flow="redirect")
        tx.provider_reference = "ORDER123"
        tx._set_pending()
        self.env["payment.transaction"]._handle_notification_data(
            "sequra",
            {
                "event": "cancelled",
                "order_ref": "ORDER123",
                "order_ref_1": tx.reference,
            },
        )
        self.assertEqual(tx.state, "cancel")

    @mute_logger(
        "odoo.addons.payment_sequra.models.payment_transaction",
        "odoo.addons.payment.models.payment_transaction",
    )
    def test_cancellation_does_not_touch_done_transaction(self):
        tx = self._create_transaction(flow="redirect")
        tx.provider_reference = "ORDER123"
        with patch(
            "odoo.addons.payment_sequra.models.payment_provider."
            "PaymentProvider._sequra_make_request",
            return_value=self._create_mock_sequra_update_response(),
        ):
            tx._process_notification_data(self.redirect_notification_data)
        self.assertEqual(tx.state, "done")
        tx._process_notification_data({"event": "cancelled", "order_ref": "ORDER123"})
        self.assertEqual(tx.state, "done")

    @mute_logger(
        "odoo.addons.payment_sequra.models.payment_transaction",
        "odoo.addons.payment_sequra.controllers.main",
    )
    def test_webhook_controller_post_cancels_transaction(self):
        tx = self._create_transaction(flow="redirect")
        tx.provider_reference = "ORDER-HTTP-1"
        tx._set_pending()
        response = self.url_open(
            "/payment/sequra/webhook",
            data={
                "charset": "UTF-8",
                "event": "cancelled",
                "order_ref": "ORDER-HTTP-1",
                "order_ref_1": tx.reference,
            },
        )
        self.assertEqual(response.status_code, 200)
        tx.invalidate_recordset()
        self.assertEqual(tx.state, "cancel")

    def test_url_encoding_in_redirect_payload(self):
        tx = self._create_transaction(flow="redirect")
        payload = tx._sequra_prepare_order_request_payload()
        encoded_ref = url_quote(tx.reference)
        self.assertIn(
            tx.reference, payload["order"]["merchant_reference"]["order_ref_1"]
        )
        self.assertNotIn(" ", encoded_ref)

    @mute_logger("odoo.addons.payment_sequra.models.payment_transaction")
    def test_complete_shopping_cart_flow(self):
        sale_order = self._create_simple_sale_order(quantity=3, price_unit=75.0)
        tx = self._create_transaction(flow="redirect")
        tx.sale_order_ids = sale_order
        with patch(
            "odoo.addons.payment_sequra.models.payment_provider.PaymentProvider._sequra_make_request",
            return_value=self._create_mock_sequra_order_response(
                self.SEQURA_CART_ORDER_ID
            ),
        ):
            rendering_values = tx._get_specific_rendering_values({})
        self.assertIn("api_url", rendering_values)
        self.assertIn("/embedded_form", rendering_values["api_url"])
        self.assertEqual(tx.provider_reference, self.SEQURA_CART_ORDER_ID)
        notification_data = self._create_sequra_notification_data(
            self.SEQURA_CART_ORDER_ID, state="approved"
        )
        with patch(
            "odoo.addons.payment_sequra.models.payment_provider.PaymentProvider._sequra_make_request",
            return_value=self._create_mock_sequra_update_response(),
        ):
            tx._process_notification_data(notification_data)
        self.assertEqual(tx.state, "done")

    @mute_logger("odoo.addons.payment_sequra.models.payment_transaction")
    def test_complete_invoice_payment_flow(self):
        invoice = self._create_simple_invoice(
            lines_data=[
                {"quantity": 2, "price_unit": 150.0},
                {"quantity": 1, "price_unit": 100.0},
            ]
        )
        tx = self._create_transaction(flow="redirect")
        tx.invoice_ids = invoice
        with patch(
            "odoo.addons.payment_sequra.models.payment_provider.PaymentProvider._sequra_make_request",
            return_value=self._create_mock_sequra_order_response(
                self.SEQURA_INVOICE_ORDER_ID
            ),
        ):
            rendering_values = tx._get_specific_rendering_values({})
        self.assertIn("api_url", rendering_values)
        self.assertTrue(rendering_values["api_url"].endswith("/embedded_form"))
        self.assertEqual(tx.provider_reference, self.SEQURA_INVOICE_ORDER_ID)
        notification_data = self._create_sequra_notification_data(
            self.SEQURA_INVOICE_ORDER_ID, state="pending"
        )
        with patch(
            "odoo.addons.payment_sequra.models.payment_provider.PaymentProvider._sequra_make_request",
            return_value=self._create_mock_sequra_update_response(),
        ):
            tx._process_notification_data(notification_data)
        self.assertEqual(tx.state, "pending")
        notification_data_approved = self._create_sequra_notification_data(
            self.SEQURA_INVOICE_ORDER_ID, state="approved"
        )
        with patch(
            "odoo.addons.payment_sequra.models.payment_provider.PaymentProvider._sequra_make_request",
            return_value=self._create_mock_sequra_update_response(),
        ):
            tx._process_notification_data(notification_data_approved)
        self.assertEqual(tx.state, "done")
