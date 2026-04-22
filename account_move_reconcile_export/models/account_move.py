# Copyright 2026 Tecnativa - Christian Ramos
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import Command, api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    reconciled_move_ids = fields.Many2many(
        "account.move",
        string="Reconciled Moves",
        compute="_compute_reconcile_move_ids",
    )

    @api.depends("move_type", "line_ids.amount_residual")
    def _compute_reconcile_move_ids(self):
        for move in self:
            if move.state == "posted" and move.is_invoice(include_receipts=True):
                reconciled_partials = move.sudo()._get_all_reconciled_invoice_partials()
                move_ids = [
                    partial["aml"].move_id.id for partial in reconciled_partials
                ]
                move.reconciled_move_ids = [Command.set(move_ids)]
            else:
                move.reconciled_move_ids = [Command.clear()]
