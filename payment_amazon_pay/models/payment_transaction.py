import logging

from odoo import fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    amazon_pay_checkout_session_id = fields.Char(readonly=True)
    amazon_pay_charge_permission_id = fields.Char(readonly=True)
    amazon_pay_charge_id = fields.Char(readonly=True)
    amazon_pay_refund_id = fields.Char(readonly=True)

    def _get_specific_processing_values(self, processing_values):
        res = super()._get_specific_processing_values(processing_values)
        if self.provider_code != "amazon_pay":
            return res

        btn = self.provider_id._amazon_pay_get_button_payload(self)
        return {
            **res,
            "checkout_js_url": btn["checkout_js_url"],
            "amazon_pay_cfg": {
                "merchantId": btn["merchant_id"],
                "publicKeyId": btn["public_key_id"],
                "ledgerCurrency": btn["ledger_currency"],
                "checkoutLanguage": btn["checkout_language"],
                "productType": "PayOnly",
                "placement": "Checkout",
                "buttonColor": "Gold",
                "sandbox": btn["sandbox"],
                "createCheckoutSessionConfig": {
                    "payloadJSON": btn["payload_json"],
                    "signature": btn["signature"],
                    "publicKeyId": btn["public_key_id"],
                },
            },
        }

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != "amazon_pay" or len(tx) == 1:
            return tx

        reference = notification_data.get(
            "merchantReferenceId"
        ) or notification_data.get("reference")
        checkout_session_id = notification_data.get("checkoutSessionId")
        charge_id = notification_data.get("chargeId")
        domain = [("provider_code", "=", "amazon_pay")]
        if reference:
            domain.append(("reference", "=", reference))
        elif checkout_session_id:
            domain.append(("amazon_pay_checkout_session_id", "=", checkout_session_id))
        elif charge_id:
            domain.append(("amazon_pay_charge_id", "=", charge_id))
        tx = self.search(domain, limit=1)
        if not tx:
            raise ValidationError(
                self.env._("Amazon Pay: no transaction found for the received data.")
            )
        return tx

    def _process_notification_data(self, notification_data):
        super()._process_notification_data(notification_data)
        if self.provider_code != "amazon_pay":
            return

        # No status data yet: this is a return URL callback, complete the session
        if not notification_data.get("statusDetails") and not notification_data.get(
            "status"
        ):
            checkout_session_id = (
                notification_data.get("checkoutSessionId")
                or self.amazon_pay_checkout_session_id
            )
            if not checkout_session_id:
                self._set_error(
                    self.env._("Amazon Pay did not return a checkout session id.")
                )
                return
            try:
                data = self.provider_id._amazon_pay_complete_checkout_session(
                    self, checkout_session_id
                )
            except Exception:
                _logger.exception(
                    "Amazon Pay completion failed for transaction %s", self.reference
                )
                try:
                    data = self.provider_id._amazon_pay_get_checkout_session(
                        checkout_session_id
                    )
                except Exception:
                    _logger.exception(
                        "Amazon Pay: failed to get checkout session %s",
                        checkout_session_id,
                    )
                    self._set_error(
                        self.env._("Amazon Pay: could not retrieve the payment status.")
                    )
                    return
            notification_data.update(data)

        received_ref = (notification_data.get("merchantMetadata") or {}).get(
            "merchantReferenceId"
        )
        if received_ref and received_ref != self.reference:
            self._set_error(
                self.env._("Amazon Pay: the payment does not match this order.")
            )
            return
        charge_amount = (notification_data.get("paymentDetails") or {}).get(
            "chargeAmount"
        ) or {}
        received_amount = charge_amount.get("amount")
        received_currency = charge_amount.get("currencyCode")
        if received_amount is not None and (
            self.currency_id.compare_amounts(float(received_amount), self.amount) != 0
            or (received_currency and received_currency != self.currency_id.name)
        ):
            self._set_error(
                self.env._("Amazon Pay: the paid amount does not match this order.")
            )
            return

        self.amazon_pay_checkout_session_id = (
            notification_data.get("checkoutSessionId")
            or self.amazon_pay_checkout_session_id
        )
        self.amazon_pay_charge_permission_id = (
            notification_data.get("chargePermissionId")
            or self.amazon_pay_charge_permission_id
        )
        self.amazon_pay_charge_id = (
            notification_data.get("chargeId") or self.amazon_pay_charge_id
        )
        self.provider_reference = (
            self.amazon_pay_charge_id
            or self.amazon_pay_charge_permission_id
            or self.amazon_pay_checkout_session_id
        )

        status_details = notification_data.get("statusDetails") or {}
        state = status_details.get("state") or notification_data.get("status")
        reason = (
            status_details.get("reasonDescription")
            or status_details.get("reasonCode")
            or notification_data.get("reasonDescription")
            or notification_data.get("reasonCode")
        )
        http_status = notification_data.get("_http_status")

        if state == "Completed":
            self._set_done()
        elif state in ("AuthorizationInitiated", "CaptureInitiated", "Pending", "Open"):
            self._set_pending(state_message=reason)
        elif state in ("Canceled", "Cancelled"):
            self._set_canceled(state_message=reason)
        elif state in ("Declined", "Closed"):
            self._set_error(reason or self.env._("Amazon Pay declined the payment."))
        elif http_status in (200, 202) and self.amazon_pay_charge_id:
            if http_status == 202:
                self._set_pending(state_message=reason)
            else:
                self._set_done()
        else:
            self._set_error(
                reason
                or self.env._("Amazon Pay returned an unexpected state: %s")
                % (state or "unknown")
            )

    def _send_refund_request(self, amount_to_refund=None):
        if self.provider_code != "amazon_pay":
            return super()._send_refund_request(amount_to_refund=amount_to_refund)

        source_tx = self.source_transaction_id
        if not source_tx or not source_tx.amazon_pay_charge_id:
            raise ValidationError(
                self.env._("Amazon Pay charge ID is missing on the source transaction.")
            )

        response = self.provider_id._amazon_pay_create_refund(
            source_tx.amazon_pay_charge_id,
            abs(amount_to_refund or self.amount),
            self.currency_id,
        )
        self.amazon_pay_refund_id = response.get("refundId")
        self.provider_reference = self.amazon_pay_refund_id
        status = (response.get("statusDetails") or {}).get("state") or response.get(
            "status"
        )
        if status in ("RefundInitiated", "Pending"):
            self._set_pending(state_message=status)
        elif status in ("Completed", "Refunded"):
            self._set_done()
        else:
            self._set_error(
                status or self.env._("Amazon Pay did not accept the refund request.")
            )
