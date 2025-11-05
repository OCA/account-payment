# Copyright 2025 Juan Carlos Oñate - Tecnativa <juancarlos.onate@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _action_done(self):
        res = super()._action_done()
        self._sequra_notify_shipment()
        return res

    def _sequra_notify_shipment(self):
        # Notify SeQura when the full order is shipped.
        for picking in self.filtered("sale_id"):
            transactions = (
                self.env["payment.transaction"]
                .sudo()
                .search(
                    [
                        ("sale_order_ids", "in", picking.sale_id.ids),
                        ("provider_code", "=", "sequra"),
                        ("state", "in", ["done", "authorized"]),
                    ]
                )
            )
            for tx in transactions:
                if not tx.provider_reference:
                    raise UserError(
                        self.env._(
                            "SeQura: Cannot send shipment notification for "
                            "transaction %s - missing provider_reference"
                        )
                        % tx.reference
                    )
                payload = self._sequra_prepare_shipment_payload(tx)
                endpoint = (
                    f"/merchants/{tx.provider_id.sequra_merchant_id}"
                    f"/orders/{tx.reference}"
                )
                response = tx.provider_id._sequra_make_request(
                    endpoint=endpoint,
                    payload=payload,
                    method="PUT",
                )
                # SeQura accepts 200, 202, 204 as success codes
                if response.status_code not in (200, 202, 204):
                    raise UserError(
                        self.env._(
                            "SeQura: Shipment notification failed for %s. "
                            "Status: %s, Response: %s"
                        )
                        % (tx.reference, response.status_code, response.text)
                    )

    def _sequra_prepare_shipment_payload(self, transaction):
        """Prepare the payload for SeQura shipment notification.

        When the full order is shipped, we send:
        - unshipped_cart: empty (order_total_with_tax = 0, items = [])
        - shipped_cart: all items from the original cart
        """
        payload = transaction._sequra_prepare_order_request_payload()
        items = transaction._get_sequra_items()
        currency = transaction.currency_id.name or "EUR"
        total = int(transaction.amount * 100)
        payload["order"].pop("cart", None)
        payload["order"]["unshipped_cart"] = {
            "currency": currency,
            "order_total_with_tax": 0,
            "items": [],
        }
        payload["order"]["shipped_cart"] = {
            "currency": currency,
            "order_total_with_tax": total,
            "items": items,
        }
        return payload
