# Copyright 2025 Juan Carlos Oñate - Tecnativa <juancarlos.onate@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import logging
import platform

from werkzeug import urls

import odoo.release
from odoo import models
from odoo.exceptions import ValidationError
from odoo.http import request

from ..controllers.main import SequraController

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    def _get_specific_rendering_values(self, processing_values):
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != "sequra":
            return res
        payload = self._sequra_prepare_order_request_payload()
        response = self.provider_id._sequra_make_request("/orders", payload=payload)
        location = response.headers.get("Location")
        if not location:
            raise ValidationError(
                self.env._("SeQura did not return a Location header. Response: %s")
                % response.text
            )
        self.provider_reference = location.rstrip("/").split("/")[-1]
        checkout_url = f"{location.rstrip('/')}/embedded_form"
        return {"api_url": checkout_url, "product": self.payment_method_id.code}

    def _get_sequra_delivery_name(self):
        order = self.sale_order_ids[:1]
        carrier = getattr(order, "carrier_id", None)
        if carrier and getattr(carrier, "name", None):
            return carrier.name
        return self.env._("Standard delivery")

    def _get_sequra_items(self):
        self.ensure_one()
        order = self.sale_order_ids[:1]
        if order:
            return [
                {
                    "reference": line.product_id.id,
                    "name": line.product_id.name,
                    "quantity": int(line.product_uom_qty),
                    "price_with_tax": int(line.price_reduce_taxinc * 100),
                    "total_with_tax": int(line.price_total * 100),
                    "downloadable": line.product_id.type == "service",
                }
                for line in order.order_line.filtered(
                    lambda line: not line.display_type
                )
            ]
        invoice = self.invoice_ids[:1]
        if invoice:
            return [
                {
                    "reference": line.product_id.id,
                    "name": line.product_id.name,
                    "quantity": int(line.quantity),
                    "price_with_tax": int(line.price_total * 100),
                    "total_with_tax": int(line.price_total * 100),
                    "downloadable": line.product_id.type == "service",
                }
                for line in invoice.invoice_line_ids.filtered(
                    lambda line: line.display_type not in ("line_note", "line_section")
                )
            ]

    def _sequra_prepare_order_request_payload(self):
        # https://docs.sequrapi.com/checkout/order_documentation.html
        self.ensure_one()
        base_url = self.provider_id.get_base_url()
        notify_url = urls.url_join(base_url, SequraController._notify_url)
        return_url = urls.url_join(base_url, SequraController._return_url)
        sanitized_reference = urls.url_quote(self.reference)
        abort_url = urls.url_join(
            base_url, f"{SequraController._abort_url}/{sanitized_reference}"
        )
        webhook_url = urls.url_join(base_url, SequraController._webhook_url)
        environ = {}
        if request and hasattr(request, "httprequest"):
            environ = request.httprequest.environ
        order = self.sale_order_ids[:1]
        if order:
            partner = order.partner_id
            partner_invoice = order.partner_invoice_id
            partner_shipping = order.partner_shipping_id
        else:
            partner = self.partner_id
            partner_invoice = partner
            partner_shipping = partner
        return {
            "order": {
                "state": "",
                "merchant": {
                    "id": self.provider_id.sequra_merchant_id,
                    "notify_url": notify_url,
                    "return_url": return_url,
                    "abort_url": abort_url,
                    "events_webhook": {"url": webhook_url},
                },
                "merchant_reference": {
                    "order_ref_1": self.reference,
                },
                "cart": {
                    "currency": self.currency_id.name or "EUR",
                    "gift": False,
                    "order_total_with_tax": int(self.amount * 100),
                    "items": self._get_sequra_items(),
                },
                "customer": {
                    "given_names": partner.name,
                    "surnames": partner.name,
                    "email": partner.email or "noemail@example.com",
                    "logged_in": "unknown",
                    "language_code": (partner.lang or "es_ES").replace("_", "-"),
                    "ip_number": environ.get("HTTP_X_FORWARDED_FOR")
                    or environ.get("REMOTE_ADDR")
                    or "127.0.0.1",
                    "user_agent": environ.get("HTTP_USER_AGENT"),
                },
                "delivery_method": {
                    "name": self._get_sequra_delivery_name(),
                },
                "delivery_address": {
                    "given_names": partner_shipping.name,
                    "surnames": partner_shipping.name,
                    "company": partner_shipping.company_name or "N/A",
                    "address_line_1": partner_shipping.street or "N/A",
                    "address_line_2": partner_shipping.street2 or "N/A",
                    "postal_code": partner_shipping.zip or "00000",
                    "city": partner_shipping.city or "Unknown",
                    "country_code": partner_shipping.country_id.code or "ES",
                },
                "invoice_address": {
                    "given_names": partner_invoice.name,
                    "surnames": partner_invoice.name,
                    "company": partner_invoice.company_name or "N/A",
                    "address_line_1": partner_invoice.street or "N/A",
                    "address_line_2": partner_invoice.street2 or "N/A",
                    "postal_code": partner_invoice.zip or "00000",
                    "city": partner_invoice.city or "Unknown",
                    "country_code": partner_invoice.country_id.code or "ES",
                },
                "gui": {
                    "layout": "smartphone"
                    if environ.get("HTTP_SEC_CH_UA_MOBILE") == "?1"
                    else "desktop"
                },
                "platform": {
                    "name": base_url,
                    "version": odoo.release.version,
                    "uname": platform.uname().system,
                    "db_name": self.env.cr.dbname,
                    "db_version": str(self.env.cr._cnx.server_version),
                },
            }
        }

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != "sequra" or len(tx) == 1:
            return tx
        reference = notification_data.get("order_ref")
        if not reference:
            raise ValidationError(
                self.env._("SeQura: Received data with missing reference.")
            )
        tx = self.search(
            [("provider_reference", "=", reference), ("provider_code", "=", "sequra")],
            limit=1,
        )
        if not tx:
            raise ValidationError(
                self.env._(
                    "SeQura: No transaction found matching reference %s.", reference
                )
            )
        return tx

    def _sequra_update_order_state(self, state):
        self.ensure_one()
        if not self.provider_reference:
            _logger.error(
                "SeQura: Missing provider_reference for tx %s", self.reference
            )
            return False
        base_url = (
            f"{self.provider_id._sequra_get_base_url()}/orders/"
            f"{self.provider_reference}"
        )
        payload = self._sequra_prepare_order_request_payload()
        payload["order"]["state"] = state
        try:
            response = self.provider_id._sequra_make_request(
                base_url,
                method="PUT",
                payload=payload,
            )
            if response.status_code == 200:
                return response
            elif response.status_code == 409:
                _logger.warning(
                    "SeQura responded with 409 Conflict for %s", self.reference
                )
            elif response.status_code == 410:
                _logger.warning("SeQura responded with 410 Gone for %s", self.reference)
            else:
                _logger.error(
                    "Unexpected SeQura response (%s): %s",
                    response.status_code,
                    response.text,
                )
        except Exception:
            _logger.exception("Error sending PUT to SeQura for tx %s", self.reference)
        return response

    def _process_notification_data(self, notification_data):
        super()._process_notification_data(notification_data)
        if self.provider_code != "sequra":
            return
        self.ensure_one()
        payment_status = (
            notification_data.get("sq_state")
            or notification_data.get("state")
            or notification_data.get("event")
        )
        if not payment_status:
            raise ValidationError(self.env._("SeQura: Missing payment status."))
        if payment_status == "cancelled":
            self._set_canceled(
                state_message=self.env._(
                    "Cancelled by SeQura: the financing was not granted."
                )
            )
            return
        state = (
            "confirmed" if payment_status in ("approved", "confirmed") else "on_hold"
        )
        response = self._sequra_update_order_state(state)
        if payment_status == "approved" and response.ok:
            self._set_done()
        elif payment_status in ("pending", "needs_review", "on_hold") and response.ok:
            self._set_pending()
        elif not response.ok:
            _logger.error(
                "SeQura: Failed to update order %s to %s. Response: %s",
                self.reference,
                state,
                response.text,
            )
            self._set_error(
                self.env._(
                    "SeQura update failed (%s %s): %s",
                    response.status_code,
                    response.reason,
                    response.text,
                )
            )
        else:
            _logger.warning(
                "SeQura: Received unrecognized payment status '%s' for tx %s",
                payment_status,
                self.reference,
            )
            self._set_error(
                self.env._("Unknown SeQura payment status: %s", payment_status)
            )
