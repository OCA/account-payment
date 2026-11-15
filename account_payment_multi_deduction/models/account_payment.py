# Copyright 2026 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    def _prepare_move_lines_per_type(
        self, write_off_line_vals=None, force_balance=None
    ):
        """Keep the deductions on the journal entry of the payment.

        - Core resync collapses the write-off lines into one: re-expand them.
        - Core drops the write-off lines of a payment with withholding lines,
          so the deducted amount stays open on the invoice: keep them and
          settle them on the counterpart line.
        """
        # A single dict means core resync collapsed the write-off lines;
        # several dicts are explicit caller values and must be kept.
        if write_off_line_vals and len(write_off_line_vals) == 1:
            deduct_lines = self.move_id.line_ids.filtered("is_writeoff")
            if deduct_lines:
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
        deduct_line_vals = [
            vals for vals in write_off_line_vals or [] if vals.get("is_writeoff")
        ]
        if not deduct_line_vals or not self._prepare_move_withholding_lines({}):
            return super()._prepare_move_lines_per_type(
                write_off_line_vals=write_off_line_vals, force_balance=force_balance
            )
        res = super()._prepare_move_lines_per_type()
        counterpart_vals = res["counterpart_lines"][0]
        counterpart_vals["amount_currency"] -= sum(
            vals["amount_currency"] for vals in deduct_line_vals
        )
        counterpart_vals["balance"] -= sum(vals["balance"] for vals in deduct_line_vals)
        res["write_off_lines"] = deduct_line_vals
        return res
