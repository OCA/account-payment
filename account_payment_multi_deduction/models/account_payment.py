# Copyright 2020 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    is_multi_deduction = fields.Boolean()

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
        """Split amount to multi payment deduction
        Concept:
        * Process by payment difference 'Mark as fully paid' and keep value is paid
        * Process by each deduction and keep value is deduction
        * Combine all process and return list
        """
        self.ensure_one()
        check_keys = self._get_check_key_list()
        update_keys = self._get_update_key_list()
        # payment difference
        if isinstance(write_off_line_vals, dict) and write_off_line_vals:
            line_vals_list = super()._prepare_move_line_default_vals(
                write_off_line_vals
            )
            # add analytic on line_vals_list
            self._update_vals_writeoff(
                write_off_line_vals, line_vals_list, check_keys, update_keys
            )
            return line_vals_list
        # multi deduction writeoff
        if isinstance(write_off_line_vals, list) and write_off_line_vals:
            origin_writeoff_amount = write_off_line_vals[0]["amount"]
            amount_total = sum(writeoff["amount"] for writeoff in write_off_line_vals)
            write_off_line_vals[0]["amount"] = amount_total
            # cast it to 'Mark as fully paid'
            write_off_reconcile = write_off_line_vals[0]
            line_vals_list = super()._prepare_move_line_default_vals(
                write_off_reconcile
            )
            line_vals_list.pop(-1)
            # rollback to origin
            write_off_line_vals[0]["amount"] = origin_writeoff_amount
            multi_deduct_list = [
                super(AccountPayment, self)._prepare_move_line_default_vals(
                    writeoff_line
                )[-1]
                for writeoff_line in write_off_line_vals
            ]
            line_vals_list.extend(multi_deduct_list)
            # add analytic on line_vals_list
            for writeoff_line in write_off_line_vals:
                self._update_vals_writeoff(
                    writeoff_line, line_vals_list, check_keys, update_keys
                )
        else:
            line_vals_list = super()._prepare_move_line_default_vals(
                write_off_line_vals
            )
        return line_vals_list

    def _synchronize_from_moves(self, changed_fields):
        ctx = self._context.copy()
        if all(rec.is_multi_deduction for rec in self):
            ctx["skip_account_move_synchronization"] = True
        return super(
            AccountPayment,
            self.with_context(**ctx),
        )._synchronize_from_moves(changed_fields)
