import json
import logging

from odoo import http
from odoo.exceptions import ValidationError
from odoo.http import request

_logger = logging.getLogger(__name__)


def _get_tx(notification_data):
    return (
        request.env["payment.transaction"]
        .sudo()
        ._get_tx_from_notification_data("amazon_pay", notification_data)
    )


class AmazonPayController(http.Controller):
    @http.route(
        "/payment/amazon_pay/return",
        type="http",
        auth="public",
        methods=["GET"],
        csrf=False,
        save_session=False,
    )
    def amazon_pay_return(self, reference=None, amazonCheckoutSessionId=None, **kwargs):
        request.env["payment.transaction"].sudo()._handle_notification_data(
            "amazon_pay",
            {"reference": reference, "checkoutSessionId": amazonCheckoutSessionId},
        )
        return request.redirect("/payment/status")

    @http.route(
        "/payment/amazon_pay/cancel",
        type="http",
        auth="public",
        methods=["GET"],
        csrf=False,
        save_session=False,
    )
    def amazon_pay_cancel(self, reference=None, amazonCheckoutSessionId=None, **kwargs):
        request.env["payment.transaction"].sudo()._handle_notification_data(
            "amazon_pay",
            {
                "reference": reference,
                "checkoutSessionId": amazonCheckoutSessionId,
                "statusDetails": {"state": "Canceled"},
            },
        )
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
            return request.make_response(
                "invalid", headers=[("Content-Type", "text/plain")]
            )

        data = payload.get("Object") or payload
        object_type = data.get("ObjectType") or data.get("objectType")
        object_id = data.get("ObjectId") or data.get("objectId")
        charge_id = data.get("chargeId")
        refund_id = data.get("refundId")

        try:
            tx = _get_tx({"checkoutSessionId": object_id, "chargeId": charge_id})
        except ValidationError:
            return request.make_response(
                "ignored", headers=[("Content-Type", "text/plain")]
            )

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
