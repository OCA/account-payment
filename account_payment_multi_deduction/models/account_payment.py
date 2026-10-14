# Copyright 2026 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    def _prepare_move_lines_per_type(
        self, write_off_line_vals=None, force_balance=None
    ):
        """Re-expand multi deduction write-off lines collapsed by core resync."""
        if write_off_line_vals and len(write_off_line_vals) == 1:
            deduct_lines = self.move_id.line_ids.filtered("is_writeoff")
            if len(deduct_lines) > 1:
                write_off_line_vals = [
                    {
                        "name": line.name,
                        "account_id": line.account_id.id,
                        "partner_id": line.partner_id.id,
                        "currency_id": line.currency_id.id,
                        "amount_currency": line.amount_currency,
                        "balance": line.balance,
                        "analytic_distribution": line.analytic_distribution,
                        "is_writeoff": True,
                    }
                    for line in deduct_lines
                ]
        return super()._prepare_move_lines_per_type(
            write_off_line_vals=write_off_line_vals, force_balance=force_balance
        )
