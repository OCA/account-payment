from odoo import _, fields, models
from odoo.exceptions import ValidationError


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    amazon_pay_checkout_session_id = fields.Char(readonly=True)
    amazon_pay_charge_permission_id = fields.Char(readonly=True)
    amazon_pay_charge_id = fields.Char(readonly=True)
    amazon_pay_refund_id = fields.Char(readonly=True)

    def _get_specific_rendering_values(self, processing_values):
        rendering_values = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != "amazon_pay":
            return rendering_values

        response = self.provider_id._amazon_pay_create_checkout_session(self)
        checkout_session_id = response.get("checkoutSessionId")
        redirect_url = (
            response.get("webCheckoutDetails", {}).get("amazonPayRedirectUrl")
            or response.get("amazonPayRedirectUrl")
        )
        if not redirect_url:
            raise ValidationError(_("Amazon Pay did not return a redirect URL."))

        self.amazon_pay_checkout_session_id = checkout_session_id
        self.provider_reference = checkout_session_id
        return {
            **rendering_values,
            "api_url": redirect_url,
            "http_method": "get",
        }

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != "amazon_pay" or len(tx) == 1:
            return tx

        reference = notification_data.get("merchantReferenceId") or notification_data.get(
            "reference"
        )
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
            raise ValidationError(_("Amazon Pay: no transaction found for the received data."))
        return tx

    def _process_notification_data(self, notification_data):
        super()._process_notification_data(notification_data)
        if self.provider_code != "amazon_pay":
            return

        payment_method = self.env["payment.method"].search(
            [("code", "=", "amazon_pay")], limit=1
        )
        if payment_method:
            self.payment_method_id = payment_method

        self.amazon_pay_checkout_session_id = (
            notification_data.get("checkoutSessionId") or self.amazon_pay_checkout_session_id
        )
        self.amazon_pay_charge_permission_id = (
            notification_data.get("chargePermissionId") or self.amazon_pay_charge_permission_id
        )
        self.amazon_pay_charge_id = notification_data.get("chargeId") or self.amazon_pay_charge_id
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
            self._set_error(reason or _("Amazon Pay declined the payment."))
        elif http_status in (200, 202) and self.amazon_pay_charge_id:
            if http_status == 202:
                self._set_pending(state_message=reason)
            else:
                self._set_done()
        else:
            self._set_error(
                reason or _("Amazon Pay returned an unexpected state: %s") % (state or "unknown")
            )

    def _send_refund_request(self, amount_to_refund=None):
        if self.provider_code != "amazon_pay":
            return super()._send_refund_request(amount_to_refund=amount_to_refund)

        source_tx = self.source_transaction_id
        if not source_tx or not source_tx.amazon_pay_charge_id:
            raise ValidationError(_("Amazon Pay charge ID is missing on the source transaction."))

        response = self.provider_id._amazon_pay_create_refund(
            source_tx.amazon_pay_charge_id,
            abs(amount_to_refund or self.amount),
            self.currency_id,
        )
        self.amazon_pay_refund_id = response.get("refundId")
        self.provider_reference = self.amazon_pay_refund_id
        status = (response.get("statusDetails") or {}).get("state") or response.get("status")
        if status in ("RefundInitiated", "Pending"):
            self._set_pending(state_message=status)
        elif status in ("Completed", "Refunded"):
            self._set_done()
        else:
            self._set_error(status or _("Amazon Pay did not accept the refund request."))
