# Copyright 2021 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    def _get_check_key_list(self):
        return ["name", "account_id"]

    def _get_update_key_list(self):
        return ["analytic_account_id", "analytic_tag_ids"]

    def _update_vals_writeoff(
        self, write_off_line_vals, line_vals_list, check_keys, update_keys
    ):
        for line_vals in line_vals_list:
            if all(
                line_vals[check_key] == write_off_line_vals[check_key]
                for check_key in check_keys
            ):
                for update_key in update_keys:
                    line_vals[update_key] = write_off_line_vals[update_key]
                break

    def _prepare_move_line_default_vals(self, write_off_line_vals=None):
        self.ensure_one()
        line_vals_list = super()._prepare_move_line_default_vals(write_off_line_vals)
        # payment difference
        if isinstance(write_off_line_vals, dict) and write_off_line_vals:
            check_keys = self._get_check_key_list()
            update_keys = self._get_update_key_list()
            self._update_vals_writeoff(
                write_off_line_vals, line_vals_list, check_keys, update_keys
            )
        return line_vals_list
