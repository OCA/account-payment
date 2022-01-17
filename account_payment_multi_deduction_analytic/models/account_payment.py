# Copyright 2021 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    def _prepare_move_line_default_vals(self, write_off_line_vals=None):
        self.ensure_one()
        line_vals_list = super()._prepare_move_line_default_vals(write_off_line_vals)
        # multi deduction writeoff
        if isinstance(write_off_line_vals, list) and write_off_line_vals:
            check_keys = self._get_check_key_list()
            update_keys = self._get_update_key_list()
            for writeoff_line in write_off_line_vals:
                self._update_vals_writeoff(
                    writeoff_line, line_vals_list, check_keys, update_keys
                )
        return line_vals_list
