# Copyright 2024 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    to_auto_reconcile = fields.Many2many(
        comodel_name="account.move.line",
        domain=lambda self: [
            ("account_id.user_type_id.type", "in", ("receivable", "payable"))
        ],
    )

    def action_post(self):
        res = super().action_post()
        # Auto reconcile
        if self.to_auto_reconcile:
            to_process = [
                {
                    "payment": self,
                    "to_reconcile": self.to_auto_reconcile,
                    "batch": {
                        "lines": self.to_auto_reconcile,
                    },
                }
            ]
            self.env["account.payment.register"]._reconcile_payments(to_process)
            if not self.env.context.get("skip_clear_auto_reconcile", False):
                self.to_auto_reconcile = False
        return res

    def action_draft(self):
        """Clear to_auto_reconcile"""
        if not self.env.context.get("skip_clear_auto_reconcile", False):
            self.to_auto_reconcile = False
        return super().action_draft()

    def action_cancel(self):
        """Clear to_auto_reconcile"""
        if not self.env.context.get("skip_clear_auto_reconcile", False):
            self.to_auto_reconcile = False
        return super().action_cancel()

    @api.model
    def _get_origin_doc(self, move_lines):
        return "move_id"

    def write(self, vals):
        # Get value of to_auto_reconcile before write
        move_lines = self.to_auto_reconcile
        #  = self._get_document()
        res = super().write(vals)
        if vals.get("to_auto_reconcile"):
            origin_doc = self._get_origin_doc(move_lines)
            val_to_reconcile = vals["to_auto_reconcile"][0][2]
            if val_to_reconcile:
                move_lines = self.env["account.move.line"].browse(val_to_reconcile)
                payment_vals = [(4, self.id)]
            else:
                payment_vals = [(3, self.id)]
            move_lines.mapped(origin_doc).write(
                {"payment_waiting_reconcile": payment_vals}
            )
        return res

    @api.model_create_multi
    def create(self, vals_list):
        payments = super().create(vals_list)
        for payment in payments:
            if payment.to_auto_reconcile:
                origin_doc = payments._get_origin_doc(payment.to_auto_reconcile)
                payment.to_auto_reconcile.mapped(origin_doc).write(
                    {"payment_waiting_reconcile": [(4, payment.id)]}
                )
        return payments
