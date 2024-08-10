# Copyright 2024 Jarsa (https://www.jarsa.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import models


class AccountPartialReconcile(models.Model):
    _inherit = "account.partial.reconcile"

    def _create_tax_cash_basis_moves(self):
        moves = super()._create_tax_cash_basis_moves()
        date = self.max_date
        if self.debit_move_id.journal_id.type in ["bank", "cash"]:
            date = self.debit_move_id.date
        elif self.credit_move_id.journal_id.type in ["bank", "cash"]:
            date = self.credit_move_id.date
        vals = {"date": date}
        if date.month != self.max_date.month:
            vals["name"] = False
        moves.write(vals)
        if date.month != self.max_date.month:
            moves._compute_name()
        return moves
