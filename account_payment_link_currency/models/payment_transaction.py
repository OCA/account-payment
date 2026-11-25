# Copyright 2026 volkantasci
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

import re

from odoo import Command, api, models


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if (
                not vals.get("invoice_ids")
                and vals.get("reference")
                and vals.get("partner_id")
            ):
                invoice = self._find_invoice_from_reference(
                    vals["reference"], vals["partner_id"]
                )
                if invoice:
                    vals["invoice_ids"] = [Command.set(invoice.ids)]
        return super().create(vals_list)

    @api.model
    def _find_invoice_from_reference(self, reference, partner_id):
        base_ref = re.sub(r"-\d+$", "", reference)
        candidate_refs = list({reference, base_ref})
        partner = self.env["res.partner"].sudo().browse(partner_id)
        if not partner.exists():
            return self.env["account.move"]
        return (
            self.env["account.move"]
            .sudo()
            .search(
                [
                    (
                        "commercial_partner_id",
                        "=",
                        partner.commercial_partner_id.id,
                    ),
                    ("move_type", "=", "out_invoice"),
                    ("state", "=", "posted"),
                    (
                        "payment_state",
                        "in",
                        ("not_paid", "in_payment", "partial"),
                    ),
                    "|",
                    ("name", "in", candidate_refs),
                    ("payment_reference", "in", candidate_refs),
                ],
                limit=1,
            )
        )
