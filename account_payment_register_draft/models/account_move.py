# Copyright 2024 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    payment_waiting_reconcile = fields.Many2many(
        comodel_name="account.payment",
        copy=False,
    )

    def action_view_payment_draft(self):
        self.ensure_one()
        return {
            "name": "Payments",
            "type": "ir.actions.act_window",
            "res_model": "account.payment",
            "view_mode": "tree,form",
            "domain": [("id", "in", self.payment_waiting_reconcile.ids)],
        }
