# Copyright 2020 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    is_multi_deduction = fields.Boolean()

    def _get_check_key_list(self):
        return ["name", "account_id"]

    def _get_update_key_list(self):
        return ["analytic_distribution"]

    def _update_vals_writeoff(
        self, write_off_line_vals, line_vals_list, check_keys, update_keys
    ):
        for line_vals in line_vals_list:
            if all(
                line_vals[check_key] == write_off_line_vals[0][check_key]
                for check_key in check_keys
            ):
                for update_key in update_keys:
                    line_vals[update_key] = write_off_line_vals[0][update_key]
                break

    def _prepare_move_line_default_vals(self, write_off_line_vals=None):
        """Split amount to multi payment deduction
        Concept:
        * Process by payment difference 'Mark as fully paid' and keep value is paid
        * Process by each deduction and keep value is deduction
        * Combine all process and return list
        """
        self.ensure_one()
        line_vals_list = super()._prepare_move_line_default_vals(write_off_line_vals)
        # payment difference
        if not self.is_multi_deduction and write_off_line_vals:
            # update writeoff when edit value in payment
            writeoff_lines = self._seek_for_lines()[2]
            if not write_off_line_vals[0].get("analytic_distribution", False):
                write_off_line_vals[0][
                    "analytic_distribution"
                ] = writeoff_lines.analytic_distribution
            # add analytic on line_vals_list
            check_keys = self._get_check_key_list()
            update_keys = self._get_update_key_list()
            self._update_vals_writeoff(
                write_off_line_vals, line_vals_list, check_keys, update_keys
            )
        return line_vals_list

    def _synchronize_from_moves(self, changed_fields):
        if any(rec.is_multi_deduction for rec in self):
            self = self.with_context(skip_account_move_synchronization=True)
        return super()._synchronize_from_moves(changed_fields)

    def write(self, vals):
        """Skip move synchronization when
        edit payment with multi deduction
        """
        if any(rec.is_multi_deduction for rec in self):
            self = self.with_context(skip_account_move_synchronization=True)
        return super().write(vals)
