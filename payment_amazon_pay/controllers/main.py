import json
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class AmazonPayController(http.Controller):
    @staticmethod
    def _find_tx(reference=None, checkout_session_id=None, charge_id=None):
        domain = [("provider_code", "=", "amazon_pay")]
        if reference:
            domain.append(("reference", "=", reference))
        elif checkout_session_id:
            domain.append(("amazon_pay_checkout_session_id", "=", checkout_session_id))
        elif charge_id:
            domain.append(("amazon_pay_charge_id", "=", charge_id))
        return request.env["payment.transaction"].sudo().search(domain, limit=1)

    @http.route(
        "/payment/amazon_pay/return",
        type="http",
        auth="public",
        methods=["GET"],
        csrf=False,
        save_session=False,
    )
    def amazon_pay_return(self, reference=None, amazonCheckoutSessionId=None, **kwargs):
        tx = self._find_tx(reference=reference, checkout_session_id=amazonCheckoutSessionId)
        if not tx:
            return request.redirect("/payment/status")

        checkout_session_id = amazonCheckoutSessionId or tx.amazon_pay_checkout_session_id
        if not checkout_session_id:
            tx._set_error("Amazon Pay did not return a checkout session id.")
            return request.redirect(tx.landing_route or "/payment/status")

        try:
            notification_data = tx.provider_id._amazon_pay_complete_checkout_session(
                tx, checkout_session_id
            )
        except Exception:
            _logger.exception(
                "Amazon Pay completion failed for transaction %s", tx.reference
            )
            notification_data = tx.provider_id._amazon_pay_get_checkout_session(
                checkout_session_id
            )

        notification_data.setdefault("reference", tx.reference)
        notification_data.setdefault("merchantReferenceId", tx.reference)
        tx._handle_notification_data("amazon_pay", notification_data)
        return request.redirect(tx.landing_route or "/payment/status")

    @http.route(
        "/payment/amazon_pay/cancel",
        type="http",
        auth="public",
        methods=["GET"],
        csrf=False,
        save_session=False,
    )
    def amazon_pay_cancel(self, reference=None, amazonCheckoutSessionId=None, **kwargs):
        tx = self._find_tx(reference=reference, checkout_session_id=amazonCheckoutSessionId)
        if tx:
            tx._set_canceled("The customer cancelled the Amazon Pay checkout.")
            return request.redirect(tx.landing_route or "/payment/status")
        return request.redirect("/payment/status")

    @http.route(
        "/payment/amazon_pay/ipn",
        type="http",
        auth="public",
        methods=["POST"],
        csrf=False,
        save_session=False,
    )
    def amazon_pay_ipn(self, **kwargs):
        raw_payload = request.httprequest.get_data(cache=False, as_text=True) or "{}"
        try:
            payload = json.loads(raw_payload)
        except json.JSONDecodeError:
            _logger.warning("Invalid Amazon Pay IPN payload: %s", raw_payload)
            return request.make_response("invalid", headers=[("Content-Type", "text/plain")])

        data = payload.get("Object") or payload
        object_type = data.get("ObjectType") or data.get("objectType")
        object_id = data.get("ObjectId") or data.get("objectId")
        charge_id = data.get("chargeId")
        refund_id = data.get("refundId")
        tx = self._find_tx(checkout_session_id=object_id, charge_id=charge_id)
        if not tx:
            return request.make_response("ignored", headers=[("Content-Type", "text/plain")])

        if object_type in ("CHARGE", "Charge") and charge_id:
            notification_data = tx.provider_id._amazon_pay_get_charge(charge_id)
        elif object_type in ("REFUND", "Refund") and refund_id:
            notification_data = tx.provider_id._amazon_pay_get_refund(refund_id)
        else:
            notification_data = tx.provider_id._amazon_pay_get_checkout_session(
                object_id or tx.amazon_pay_checkout_session_id
            )

        notification_data.setdefault("reference", tx.reference)
        notification_data.setdefault("merchantReferenceId", tx.reference)
        tx._handle_notification_data("amazon_pay", notification_data)
        return request.make_response("ok", headers=[("Content-Type", "text/plain")])
