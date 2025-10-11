# Copyright 2025 Open Source Integrators
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from unittest.mock import MagicMock, patch

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import HttpCase, TransactionCase


@tagged("post_install", "-at_install")
class TestEasyPay(TransactionCase):
    """Test EasyPay payment provider."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.provider = cls.env["payment.provider"].create(
            {
                "name": "EasyPay Test",
                "code": "easypay",
                "state": "test",
                "easypay_account_id": "test-account-id",
                "easypay_api_key": "test-api-key",
                "easypay_payment_method": "cc",
                "easypay_use_checkout": True,
            }
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Partner",
                "email": "test@example.com",
                "phone": "+351911234567",
            }
        )
        cls.currency = cls.env.ref("base.EUR")
        cls.payment_method = cls.env.ref("payment.payment_method_card")

    def test_provider_creation(self):
        """Test that the provider is created correctly."""
        self.assertEqual(self.provider.code, "easypay")
        self.assertEqual(self.provider.easypay_payment_method, "cc")
        self.assertTrue(self.provider.easypay_use_checkout)

    def test_api_url_test_mode(self):
        """Test that the correct API URL is returned for test mode."""
        self.provider.state = "test"
        api_url = self.provider._easypay_get_api_url()
        self.assertEqual(api_url, "https://api.test.easypay.pt")

    def test_api_url_production_mode(self):
        """Test that the correct API URL is returned for production mode."""
        self.provider.state = "enabled"
        api_url = self.provider._easypay_get_api_url()
        self.assertEqual(api_url, "https://api.prod.easypay.pt")

    def test_transaction_creation(self):
        """Test that a transaction can be created."""
        tx = self.env["payment.transaction"].create(
            {
                "provider_id": self.provider.id,
                "payment_method_id": self.payment_method.id,
                "reference": "TEST-001",
                "amount": 100.0,
                "currency_id": self.currency.id,
                "partner_id": self.partner.id,
            }
        )
        self.assertEqual(tx.provider_code, "easypay")
        self.assertEqual(tx.amount, 100.0)

    @patch("requests.post")
    def test_create_checkout_session(self, mock_post):
        """Test creating a checkout session with mocked API."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "checkout-123",
            "session": "manifest-data",
            "status": "pending",
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        tx = self.env["payment.transaction"].create(
            {
                "provider_id": self.provider.id,
                "payment_method_id": self.payment_method.id,
                "reference": "TEST-CHECKOUT-001",
                "amount": 100.0,
                "currency_id": self.currency.id,
                "partner_id": self.partner.id,
            }
        )

        result = self.provider._easypay_create_checkout_session(tx.sudo())
        self.assertEqual(result["id"], "checkout-123")
        self.assertEqual(result["session"], "manifest-data")
        self.assertTrue(mock_post.called)

        # Verify the payload sent to EasyPay
        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        self.assertEqual(payload["type"], ["single"])
        self.assertEqual(payload["payment"]["methods"], ["cc"])
        self.assertEqual(payload["payment"]["currency"], "EUR")
        self.assertEqual(payload["order"]["value"], 100.0)

    def test_notification_processing_success(self):
        """Test processing a successful payment notification."""
        tx = self.env["payment.transaction"].create(
            {
                "provider_id": self.provider.id,
                "payment_method_id": self.payment_method.id,
                "reference": "TEST-002",
                "amount": 50.0,
                "currency_id": self.currency.id,
                "partner_id": self.partner.id,
            }
        )

        notification_data = {
            "id": "payment-123",
            "key": "TEST-002",
            "status": "success",
            "type": "capture",
        }

        tx._process_notification_data(notification_data)
        self.assertEqual(tx.state, "done")
        self.assertEqual(tx.easypay_payment_id, "payment-123")

    def test_notification_processing_failed(self):
        """Test processing a failed payment notification."""
        tx = self.env["payment.transaction"].create(
            {
                "provider_id": self.provider.id,
                "payment_method_id": self.payment_method.id,
                "reference": "TEST-003",
                "amount": 75.0,
                "currency_id": self.currency.id,
                "partner_id": self.partner.id,
            }
        )

        notification_data = {
            "id": "payment-456",
            "key": "TEST-003",
            "status": "failed",
            "messages": ["Payment declined"],
        }

        tx._process_notification_data(notification_data)
        self.assertEqual(tx.state, "error")

    def test_currency_validation_checkout(self):
        """Test that non-EUR currency raises ValidationError for checkout."""
        usd_currency = self.env.ref("base.USD")
        tx = self.env["payment.transaction"].create(
            {
                "provider_id": self.provider.id,
                "payment_method_id": self.payment_method.id,
                "reference": "TEST-USD-001",
                "amount": 100.0,
                "currency_id": usd_currency.id,
                "partner_id": self.partner.id,
            }
        )

        with self.assertRaises(ValidationError) as context:
            self.provider._easypay_create_checkout_session(tx.sudo())

        self.assertIn("Only EUR currency is supported", str(context.exception))

    @patch("requests.post")
    def test_create_single_payment(self, mock_post):
        """Test creating a single payment with mocked API."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "payment-789",
            "status": "pending",
            "method": {
                "type": "cc",
                "url": "https://pay.easypay.pt/xyz",
            },
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        self.provider.easypay_use_checkout = False
        tx = self.env["payment.transaction"].create(
            {
                "provider_id": self.provider.id,
                "payment_method_id": self.payment_method.id,
                "reference": "TEST-SINGLE-001",
                "amount": 50.0,
                "currency_id": self.currency.id,
                "partner_id": self.partner.id,
            }
        )

        result = self.provider._easypay_create_single_payment(tx.sudo())
        self.assertEqual(result["id"], "payment-789")
        self.assertEqual(result["method"]["url"], "https://pay.easypay.pt/xyz")
        self.assertTrue(mock_post.called)

        # Verify the payload
        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        self.assertEqual(payload["type"], "sale")
        self.assertEqual(payload["method"], "cc")
        self.assertEqual(payload["value"], 50.0)
        self.assertEqual(payload["currency"], "EUR")

    def test_currency_validation_single_payment(self):
        """Test that non-EUR currency raises ValidationError for single payment."""
        usd_currency = self.env.ref("base.USD")
        self.provider.easypay_use_checkout = False
        tx = self.env["payment.transaction"].create(
            {
                "provider_id": self.provider.id,
                "payment_method_id": self.payment_method.id,
                "reference": "TEST-USD-002",
                "amount": 75.0,
                "currency_id": usd_currency.id,
                "partner_id": self.partner.id,
            }
        )

        with self.assertRaises(ValidationError) as context:
            self.provider._easypay_create_single_payment(tx.sudo())

        self.assertIn("Only EUR currency is supported", str(context.exception))

    def test_get_tx_from_notification_data(self):
        """Test finding transaction from notification data."""
        tx = self.env["payment.transaction"].create(
            {
                "provider_id": self.provider.id,
                "payment_method_id": self.payment_method.id,
                "reference": "TEST-NOTIF-001",
                "amount": 25.0,
                "currency_id": self.currency.id,
                "partner_id": self.partner.id,
            }
        )

        notification_data = {
            "key": "TEST-NOTIF-001",
            "id": "payment-999",
        }

        found_tx = tx._get_tx_from_notification_data("easypay", notification_data)
        self.assertEqual(found_tx.id, tx.id)

    def test_notification_processing_authorized(self):
        """Test processing an authorized payment notification."""
        tx = self.env["payment.transaction"].create(
            {
                "provider_id": self.provider.id,
                "payment_method_id": self.payment_method.id,
                "reference": "TEST-AUTH-001",
                "amount": 150.0,
                "currency_id": self.currency.id,
                "partner_id": self.partner.id,
            }
        )

        notification_data = {
            "id": "payment-auth-123",
            "key": "TEST-AUTH-001",
            "status": "authorised",
            "type": "authorisation",
        }

        tx._process_notification_data(notification_data)
        self.assertEqual(tx.state, "authorized")
        self.assertEqual(tx.easypay_payment_id, "payment-auth-123")

    @patch("requests.post")
    def test_http_error_handling(self, mock_post):
        """Test that HTTP errors are properly handled and logged."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "message": "Invalid payment method",
        }
        mock_response.raise_for_status.side_effect = Exception("400 Bad Request")
        mock_post.return_value = mock_response

        tx = self.env["payment.transaction"].create(
            {
                "provider_id": self.provider.id,
                "payment_method_id": self.payment_method.id,
                "reference": "TEST-ERROR-001",
                "amount": 10.0,
                "currency_id": self.currency.id,
                "partner_id": self.partner.id,
            }
        )

        with self.assertRaises(ValidationError):
            self.provider._easypay_create_checkout_session(tx.sudo())


@tagged("post_install", "-at_install")
class TestEasyPayController(HttpCase):
    """Test EasyPay controller endpoints."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.provider = cls.env["payment.provider"].create(
            {
                "name": "EasyPay Test Controller",
                "code": "easypay",
                "state": "test",
                "easypay_account_id": "test-account-id",
                "easypay_api_key": "test-api-key",
                "easypay_payment_method": "cc",
                "easypay_use_checkout": True,
            }
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Partner Controller",
                "email": "controller@example.com",
                "phone": "+351911234567",
            }
        )
        cls.currency = cls.env.ref("base.EUR")
        cls.payment_method = cls.env.ref("payment.payment_method_card")

    @patch("requests.get")
    def test_checkout_success_callback(self, mock_get):
        """Test checkout success callback fetches payment data and updates
        transaction.
        """
        # Create transaction with checkout ID
        tx = self.env["payment.transaction"].create(
            {
                "provider_id": self.provider.id,
                "payment_method_id": self.payment_method.id,
                "reference": "TEST-SUCCESS-001",
                "amount": 99.99,
                "currency_id": self.currency.id,
                "partner_id": self.partner.id,
                "easypay_checkout_id": "checkout-success-123",
            }
        )

        # Mock the API response for fetching checkout details
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "checkout-success-123",
            "key": "TEST-SUCCESS-001",
            "status": "success",
            "type": "capture",
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Simulate the success callback
        response = self.url_open(
            "/payment/easypay/checkout/success?id=checkout-success-123"
        )

        # Verify redirect to payment status
        self.assertEqual(response.status_code, 200)

        # Verify transaction was updated
        tx.invalidate_recordset()
        self.assertEqual(tx.state, "done")
        self.assertTrue(mock_get.called)

    def test_checkout_cancel_callback(self):
        """Test checkout cancel callback sets transaction to canceled."""
        tx = self.env["payment.transaction"].create(
            {
                "provider_id": self.provider.id,
                "payment_method_id": self.payment_method.id,
                "reference": "TEST-CANCEL-001",
                "amount": 50.0,
                "currency_id": self.currency.id,
                "partner_id": self.partner.id,
            }
        )

        # Simulate the cancel callback
        response = self.url_open(
            f"/payment/easypay/checkout/cancel?reference={tx.reference}"
        )

        # Verify redirect
        self.assertEqual(response.status_code, 200)

        # Verify transaction was canceled
        tx.invalidate_recordset()
        self.assertEqual(tx.state, "cancel")
