# Copyright 2025 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.depends(
        "invoice_payment_term_id",
        "invoice_date",
        "currency_id",
        "amount_total_in_currency_signed",
        "invoice_date_due",
        "partner_id",
    )
    def _compute_needed_terms(self):
        """Add the invoice type and the partner to the context to later use it in
        the payment terms compute"""
        for move in self:
            ctx = self.env.context.copy()
            if move.partner_id and move.is_invoice(True):
                ctx.update(
                    {"partner_id": move.partner_id.id, "invoice_type": move.move_type}
                )
            super(AccountMove, move.with_context(**ctx))._compute_needed_terms()
        return True
