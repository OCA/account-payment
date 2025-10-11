# Copyright 2025 Open Source Integrators
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import logging
import pprint

from odoo import _, fields, models
from odoo.exceptions import ValidationError

from .. import const

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    easypay_payment_id = fields.Char(
        string="EasyPay Payment ID",
        help="The payment ID returned by EasyPay",
        readonly=True,
    )
    easypay_transaction_id = fields.Char(
        string="EasyPay Transaction ID",
        help="The transaction ID returned by EasyPay",
        readonly=True,
    )
    easypay_checkout_id = fields.Char(
        string="EasyPay Checkout ID",
        help="The checkout session ID returned by EasyPay",
        readonly=True,
    )
    easypay_payment_url = fields.Char(
        string="EasyPay Payment URL",
        help="The URL to redirect the customer to complete payment",
        readonly=True,
    )

    def _get_specific_processing_values(self, processing_values):
        """Override of payment to return EasyPay-specific processing values.

        Note: self.ensure_one() from `_get_processing_values`

        :param dict processing_values: The generic processing values of the transaction
        :return: The dict of provider-specific processing values
        :rtype: dict
        """
        res = super()._get_specific_processing_values(processing_values)
        if self.provider_code != "easypay":
            return res

        if self.provider_id.easypay_use_checkout:
            # Checkout flow - SDK-based inline payment
            response = self.provider_id._easypay_create_checkout_session(self.sudo())
            _logger.info("EasyPay: Checkout session response: %s", response)
            self.easypay_checkout_id = response.get("id")
            manifest = response.get("session")
            res.update(
                {
                    "checkout_manifest": manifest,
                    "checkout_id": self.easypay_checkout_id,
                    "api_url": self.provider_id._easypay_get_api_url(),
                }
            )
        else:
            # Single Payment flow - redirect to hosted page
            response = self.provider_id._easypay_create_single_payment(self.sudo())
            _logger.info("EasyPay: Single payment response: %s", response)
            self.easypay_payment_id = response.get("id")
            payment_url = response.get("method", {}).get("url")
            _logger.info(
                "EasyPay: Payment ID: %s, URL: %s", self.easypay_payment_id, payment_url
            )
            res.update(
                {
                    "easypay_payment_id": self.easypay_payment_id,
                    "easypay_payment_url": payment_url,
                }
            )
        return res

    def _get_specific_rendering_values(self, processing_values):
        """Override of payment to return EasyPay-specific rendering values.

        Note: self.ensure_one() from `_get_processing_values`

        :param dict processing_values: The generic and specific processing values
        :return: The dict of provider-specific rendering values
        :rtype: dict
        """
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != "easypay":
            return res

        if self.provider_id.easypay_use_checkout:
            # Checkout flow - pass SDK data
            res.update(
                {
                    "checkout_manifest": processing_values.get("checkout_manifest"),
                    "checkout_id": processing_values.get("checkout_id"),
                    "api_url": processing_values.get("api_url"),
                }
            )
        else:
            # Single Payment flow - pass redirect URL
            res.update(
                {
                    "easypay_payment_url": processing_values.get("easypay_payment_url"),
                }
            )
        return res

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """Override of payment to find the transaction based on EasyPay data.

        :param str provider_code: The provider code
        :param dict notification_data: The notification data
        :return: The transaction
        :rtype: recordset of `payment.transaction`
        :raise ValidationError: If the transaction is not found
        """
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != "easypay" or len(tx) == 1:
            return tx

        # Try to find transaction by reference or EasyPay IDs
        reference = notification_data.get("key")
        payment_id = notification_data.get("id")

        if reference:
            tx = self.search(
                [("reference", "=", reference), ("provider_code", "=", "easypay")]
            )
        elif payment_id:
            tx = self.search(
                [
                    "|",
                    ("easypay_payment_id", "=", payment_id),
                    ("easypay_checkout_id", "=", payment_id),
                    ("provider_code", "=", "easypay"),
                ]
            )

        if not tx:
            raise ValidationError(
                _(
                    "EasyPay: No transaction found matching reference %s.",
                    reference,
                )
            )
        return tx

    def _process_notification_data(self, notification_data):
        """Override of payment to process the notification data.

        Note: self.ensure_one() from `_handle_notification_data`

        :param dict notification_data: The notification data
        :return: None
        """
        super()._process_notification_data(notification_data)
        if self.provider_code != "easypay":
            return

        _logger.debug(
            "Processing notification for %s:\n%s",
            self.reference,
            pprint.pformat(notification_data),
        )

        # Extract relevant data from notification
        payment_id = notification_data.get("id")
        # EasyPay API uses 'payment_status' for Single Payment
        # and 'status' for other flows
        status = notification_data.get("payment_status") or notification_data.get(
            "status"
        )

        # Update transaction with EasyPay data
        if payment_id and not self.easypay_payment_id:
            self.easypay_payment_id = payment_id

        # Map 'paid' status to 'success' for consistency
        if status == "paid":
            status = "success"

        # Update the payment state
        payment_state = next(
            (
                state
                for state, easypay_statuses in const.STATUS_MAPPING.items()
                if status in easypay_statuses
            ),
            None,
        )

        if payment_state == "pending":
            self._set_pending()
        elif payment_state == "authorized":
            self._set_authorized()
        elif payment_state == "done":
            self._set_done()
        elif payment_state == "cancel":
            self._set_canceled()
        elif payment_state == "error":
            error_msg = notification_data.get("messages", ["Payment failed"])
            if isinstance(error_msg, list):
                error_msg = ", ".join(error_msg)
            self._set_error(error_msg)
        else:
            _logger.warning(
                "received notification for transaction with reference %s "
                "with unknown status: %s",
                self.reference,
                status,
            )

    def _easypay_get_payment_details(self):
        """Fetch payment details from EasyPay API.

        Note: self.ensure_one()

        :return: The payment details
        :rtype: dict
        :raise ValidationError: If no payment ID is found
        """
        self.ensure_one()

        if not self.easypay_payment_id:
            raise ValidationError(_("No EasyPay payment ID found for this transaction"))

        endpoint = f"/2.0/single/{self.easypay_payment_id}"
        return self.provider_id._easypay_make_request(endpoint, method="GET")

    def _send_refund_request(self, amount_to_refund=None):
        """Override of payment to send a refund request to EasyPay.

        Note: self.ensure_one()

        :param float amount_to_refund: The amount to refund
        :return: The refund transaction
        :rtype: recordset of `payment.transaction`
        :raise ValidationError: If no transaction ID is found
        """
        if self.provider_code != "easypay":
            return super()._send_refund_request(amount_to_refund=amount_to_refund)

        # Get the capture/transaction ID
        if not self.easypay_transaction_id:
            # Try to fetch it from the payment details
            payment_details = self._easypay_get_payment_details()
            capture_data = payment_details.get("capture", {})
            self.easypay_transaction_id = capture_data.get("id")

        if not self.easypay_transaction_id:
            raise ValidationError(_("Cannot refund: No EasyPay transaction ID found"))

        # Create refund request
        refund_amount = amount_to_refund or self.amount
        payload = {
            "transaction_id": self.easypay_transaction_id,
            "value": refund_amount,
        }

        endpoint = f"/2.0/capture/{self.easypay_transaction_id}/refund"
        response = self.provider_id._easypay_make_request(endpoint, payload)
        _logger.info(
            "refund request response for transaction with reference %s:\n%s",
            self.reference,
            pprint.pformat(response),
        )

        # Create refund transaction
        refund_tx = self._create_refund_transaction(amount_to_refund=refund_amount)
        refund_tx.easypay_payment_id = response.get("id")

        return refund_tx

    def _send_capture_request(self):
        """Override of payment to send a capture request to EasyPay.

        Note: self.ensure_one()

        :return: None
        :raise ValidationError: If no payment ID is found
        """
        if self.provider_code != "easypay":
            return super()._send_capture_request()

        if not self.easypay_payment_id:
            raise ValidationError(_("Cannot capture: No EasyPay payment ID found"))

        # Create capture request
        payload = {
            "descriptive": self.reference,
            "transaction_key": self.reference,
            "value": self.amount,
        }

        endpoint = "/2.0/capture"
        response = self.provider_id._easypay_make_request(endpoint, payload)
        _logger.info(
            "capture request response for transaction with reference %s:\n%s",
            self.reference,
            pprint.pformat(response),
        )

        self.easypay_transaction_id = response.get("id")
        self._set_done()

    def _send_void_request(self):
        """Override of payment to send a void request to EasyPay.

        Note: self.ensure_one()

        :return: None
        :raise ValidationError: If no payment ID is found
        """
        if self.provider_code != "easypay":
            return super()._send_void_request()

        if not self.easypay_payment_id:
            raise ValidationError(_("Cannot void: No EasyPay payment ID found"))

        endpoint = f"/2.0/authorisation/{self.easypay_payment_id}/void"
        response = self.provider_id._easypay_make_request(endpoint, {})
        _logger.info(
            "void request response for transaction with reference %s:\n%s",
            self.reference,
            pprint.pformat(response),
        )
        self._set_canceled()
