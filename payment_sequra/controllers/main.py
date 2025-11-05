# Copyright 2025 Juan Carlos Oñate - Tecnativa <juancarlos.onate@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class SequraController(http.Controller):
    _return_url = "/payment/sequra/return"
    _notify_url = "/payment/sequra/notify"
    _abort_url = "/payment/sequra/abort"
    _webhook_url = "/payment/sequra/webhook"

    @http.route(_return_url, type="http", methods=["GET"], auth="public", csrf=False)
    def sequra_return(self, **data):
        return request.redirect("/payment/status")

    @http.route(_notify_url, type="http", methods=["POST"], auth="public", csrf=False)
    def sequra_notify(self, **data):
        try:
            request.env["payment.transaction"].sudo()._handle_notification_data(
                "sequra", data
            )
        except Exception:
            _logger.exception("Error processing SeQura IPN")
            return request.make_response("Internal Server Error", status=500)
        return request.make_response("OK", status=200)

    @http.route(
        f"{_abort_url}/<reference>",
        type="http",
        methods=["GET"],
        auth="public",
        csrf=False,
    )
    def sequra_abort(self, reference, **data):
        tx_sudo = (
            request.env["payment.transaction"]
            .sudo()
            .search(
                [("reference", "=", reference), ("provider_code", "=", "sequra")],
                limit=1,
            )
        )
        if tx_sudo:
            tx_sudo._set_canceled()
        return request.redirect("/payment/status")

    @http.route(_webhook_url, type="http", methods=["POST"], auth="public", csrf=False)
    def sequra_webhook(self, **data):
        # SeQura only notifies cancellations here; the IPN handles the rest.
        if data.get("event") == "cancelled":
            try:
                request.env["payment.transaction"].sudo()._handle_notification_data(
                    "sequra", data
                )
            except Exception:
                _logger.exception("Error processing SeQura webhook")
                return request.make_response("Internal Server Error", status=500)
        return request.make_response("OK", status=200)
