# Copyright 2025 Open Source Integrators
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import json
import logging
import pprint

import werkzeug

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class EasyPayController(http.Controller):
    """Controller to handle EasyPay webhooks and redirects."""

    _return_url = "/payment/easypay/return"
    _webhook_url = "/payment/easypay/webhook"

    @http.route(
        _return_url,
        type="http",
        auth="public",
        methods=["GET", "POST"],
        csrf=False,
        save_session=False,
    )
    def easypay_return_from_redirect(self, **data):
        """Process the return from EasyPay after payment.

        :param dict data: The GET/POST data from EasyPay
        :return: Redirect to payment status page
        """
        # If POST with JSON body, parse it
        if (
            request.httprequest.method == "POST"
            and request.httprequest.content_type == "application/json"
        ):
            try:
                data = json.loads(request.httprequest.data.decode("utf-8"))
            except Exception as e:
                _logger.error("Error parsing JSON body: %s", e)
        _logger.info("EasyPay return endpoint called")
        _logger.debug("Request method: %s", request.httprequest.method)
        _logger.debug("Request URL: %s", request.httprequest.url)
        _logger.debug(
            "Request headers:\n%s", pprint.pformat(dict(request.httprequest.headers))
        )
        _logger.debug("Return data:\n%s", pprint.pformat(data))

        # Extract transaction reference and payment ID
        reference = data.get("key") or data.get("reference")
        payment_id = data.get("id")
        notification_type = data.get("type")

        # If no data provided in POST body, check URL query params
        if not reference and not payment_id:
            reference = request.httprequest.args.get(
                "key"
            ) or request.httprequest.args.get("reference")
            payment_id = request.httprequest.args.get("id")
            _logger.debug(
                "Checking URL params - reference: %s, payment_id: %s",
                reference,
                payment_id,
            )

        # If this is a Generic notification (has 'type' field),
        # fetch full payment details
        if payment_id and notification_type:
            _logger.info(
                "Generic notification received for %s, fetching full payment details",
                reference,
            )
            tx_sudo = (
                request.env["payment.transaction"]
                .sudo()
                .search([("reference", "=", reference)], limit=1)
            )
            if tx_sudo:
                try:
                    payment_data = tx_sudo.provider_id._easypay_make_request(
                        f"/2.0/single/{payment_id}", method="GET"
                    )
                    _logger.debug(
                        "Payment data from API:\n%s", pprint.pformat(payment_data)
                    )
                    tx_sudo._handle_notification_data("easypay", payment_data)
                    _logger.info("Transaction %s updated from API data", reference)
                except Exception as e:
                    _logger.exception("EasyPay: Error fetching payment status: %s", e)
            else:
                _logger.warning("No transaction found for reference: %s", reference)
        elif reference:
            # Direct payment data (not a Generic notification)
            tx_sudo = (
                request.env["payment.transaction"]
                .sudo()
                .search([("reference", "=", reference)], limit=1)
            )
            if tx_sudo:
                tx_sudo._handle_notification_data("easypay", data)
                _logger.info("Transaction %s updated from notification data", reference)

        return werkzeug.utils.redirect("/payment/status", code=303)

    @http.route(
        _webhook_url,
        type="json",
        auth="public",
        methods=["POST"],
        csrf=False,
        save_session=False,
    )
    def easypay_webhook(self, **data):
        """Process webhook notifications from EasyPay.

        EasyPay sends Generic notifications with: id, key, type, status, messages, date
        We fetch the full payment details from the API and process them.

        :param dict data: The webhook data from EasyPay
        :return: Empty response
        """
        _logger.info("EasyPay webhook called")
        _logger.debug("Webhook data:\n%s", pprint.pformat(data))

        try:
            # Generic notification format: {id, key, type, status, messages, date}
            payment_id = data.get("id")
            reference = data.get("key")
            notification_type = data.get("type")
            notification_status = data.get("status")

            _logger.debug(
                "Webhook - ID: %s, Key: %s, Type: %s, Status: %s",
                payment_id,
                reference,
                notification_type,
                notification_status,
            )

            if payment_id or reference:
                # Find the transaction
                tx_sudo = request.env["payment.transaction"].sudo()
                if reference:
                    tx_sudo = tx_sudo.search([("reference", "=", reference)], limit=1)
                elif payment_id:
                    tx_sudo = tx_sudo.search(
                        [
                            "|",
                            ("easypay_payment_id", "=", payment_id),
                            ("easypay_checkout_id", "=", payment_id),
                        ],
                        limit=1,
                    )

                if tx_sudo:
                    _logger.info(
                        "Webhook for %s, fetching full payment details",
                        tx_sudo.reference,
                    )
                    try:
                        payment_data = tx_sudo.provider_id._easypay_make_request(
                            f"/2.0/single/{payment_id}", method="GET"
                        )
                        _logger.debug(
                            "Payment data from API:\n%s", pprint.pformat(payment_data)
                        )
                        tx_sudo._handle_notification_data("easypay", payment_data)
                        _logger.info(
                            "Transaction %s updated from webhook", tx_sudo.reference
                        )
                    except Exception as e:
                        _logger.exception("Error fetching payment details: %s", e)
                else:
                    _logger.warning(
                        "Webhook for unknown transaction: %s", reference or payment_id
                    )
            else:
                _logger.warning("Received webhook without reference or ID")

        except Exception as e:
            _logger.exception("Error processing webhook: %s", e)

        return {}

    @http.route(
        "/payment/easypay/checkout/success",
        type="http",
        auth="public",
        methods=["GET"],
        csrf=False,
        save_session=False,
    )
    def easypay_checkout_success(self, **data):
        """Handle successful checkout completion.

        :param dict data: The GET data from checkout
        :return: Redirect to payment status page
        """
        _logger.info(
            "Checkout success from EasyPay with data:\n%s", pprint.pformat(data)
        )

        # Extract checkout ID or reference to find the transaction
        checkout_id = data.get("id")
        reference = data.get("key") or data.get("reference")

        if checkout_id or reference:
            # Find the transaction
            tx_sudo = request.env["payment.transaction"].sudo()
            if reference:
                tx_sudo = tx_sudo.search(
                    [
                        "&",
                        ("reference", "=", reference),
                        ("provider_code", "=", "easypay"),
                    ],
                    limit=1,
                )
            elif checkout_id:
                tx_sudo = tx_sudo.search(
                    [
                        "&",
                        ("easypay_checkout_id", "=", checkout_id),
                        ("provider_code", "=", "easypay"),
                    ],
                    limit=1,
                )

            if tx_sudo:
                # Fetch payment details from EasyPay API
                try:
                    endpoint = f"/2.0/checkout/{tx_sudo.easypay_checkout_id}"
                    payment_data = tx_sudo.provider_id._easypay_make_request(
                        endpoint, method="GET"
                    )
                    _logger.info(
                        "Fetched checkout details for %s:\n%s",
                        tx_sudo.reference,
                        pprint.pformat(payment_data),
                    )
                    # Process the payment data
                    tx_sudo._handle_notification_data("easypay", payment_data)
                except Exception as e:
                    _logger.exception(
                        "Error fetching checkout details for %s: %s",
                        tx_sudo.reference,
                        e,
                    )
            else:
                _logger.warning(
                    "Checkout success but transaction not found: %s",
                    reference or checkout_id,
                )

        return request.redirect("/payment/status")

    @http.route(
        "/payment/easypay/checkout/cancel",
        type="http",
        auth="public",
        methods=["GET"],
        csrf=False,
        save_session=False,
    )
    def easypay_checkout_cancel(self, **data):
        """Handle checkout cancellation.

        :param dict data: The GET data from checkout
        :return: Redirect to payment status page
        """
        _logger.info(
            "Checkout cancelled from EasyPay with data:\n%s", pprint.pformat(data)
        )

        # Try to find and cancel the transaction
        reference = data.get("key") or data.get("reference")
        if reference:
            tx_sudo = (
                request.env["payment.transaction"]
                .sudo()
                .search([("reference", "=", reference)])
            )
            if tx_sudo:
                tx_sudo._set_canceled(state_message="Payment cancelled by customer")

        return request.redirect("/payment/status")
