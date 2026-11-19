# Copyright 2026 Tecnativa - Christian Ramos
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    reconciled_move_ids = fields.Many2many(
        comodel_name="account.move",
        string="Reconciled Moves",
        compute="_compute_reconciled_move_ids",
        help="Journal entries reconciled with this invoice (payments, credit "
        "notes, write-offs...). Exportable counterpart of the read-only "
        "payments widget.",
    )

    @api.depends(
        "move_type",
        "state",
        "line_ids.amount_residual",
        "line_ids.matched_debit_ids",
        "line_ids.matched_credit_ids",
    )
    def _compute_reconciled_move_ids(self):
        for move in self:
            move_ids = set()
            if move.state == "posted" and move.is_invoice(include_receipts=True):
                # sudo() is needed to gather the partials, as in the standard
                # payments widget, but the resulting moves are filtered back
                # against the current user's access rights below.
                for partial in move.sudo()._get_all_reconciled_invoice_partials():
                    move_ids.add(partial["aml"].move_id.id)
            moves = self.env["account.move"].browse(move_ids)
            move.reconciled_move_ids = moves._filtered_access("read")
