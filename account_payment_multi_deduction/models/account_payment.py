# Copyright 2020 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    def _prepare_move_line_default_vals(self, write_off_line_vals=None):
        """Split amount to multi payment deduction
        Concept:
        * Process by payment difference 'Mark as fully paid' and keep value is paid
        * Process by each deduction and keep value is deduction
        * Combine all process and return list
        """
        self.ensure_one()
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
        else:
            line_vals_list = super()._prepare_move_line_default_vals(
                write_off_line_vals
            )
        return line_vals_list
