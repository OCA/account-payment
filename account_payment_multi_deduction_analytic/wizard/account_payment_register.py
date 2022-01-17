# Copyright 2021 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    def _prepare_deduct_move_line(self, deduct):
        vals = super()._prepare_deduct_move_line(deduct)
        vals.update(
            {
                "analytic_account_id": deduct.analytic_account_id
                and deduct.analytic_account_id.id
                or False,
                "analytic_tag_ids": deduct.analytic_tag_ids
                and [(6, 0, deduct.analytic_tag_ids.ids)]
                or False,
            }
        )
        return vals
