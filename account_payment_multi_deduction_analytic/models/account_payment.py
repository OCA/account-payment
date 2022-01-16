# Copyright 2021 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    def _get_check_key_list(self):
        return ["name", "account_id"]

    def _get_update_key_list(self):
        return ["analytic_account_id", "analytic_tag_ids"]

    def _prepare_move_line_default_vals(self, write_off_line_vals=None):
        self.ensure_one()
        line_vals_list = super()._prepare_move_line_default_vals(write_off_line_vals)
        check_keys = self._get_check_key_list()
        update_keys = self._get_update_key_list()
        # multi deduction writeoff
        if isinstance(write_off_line_vals, list) and write_off_line_vals:
            for writeoff_line in write_off_line_vals:
                for line_vals in line_vals_list:
                    if all(
                        line_vals[check_key] == writeoff_line[check_key]
                        for check_key in check_keys
                    ):
                        for update_key in update_keys:
                            line_vals[update_key] = writeoff_line[update_key]
                        break
        return line_vals_list
