# Copyright 2021 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    writeoff_analytic_account_id = fields.Many2one(
        comodel_name="account.analytic.account",
        string="Analytic Account",
        index=True,
    )
    writeoff_analytic_tag_ids = fields.Many2many(
        comodel_name="account.analytic.tag",
        string="Analytic Tags",
    )

    @api.onchange("payment_difference", "payment_difference_handling")
    def _onchange_payment_difference_handling(self):
        if self.payment_difference_handling == "reconcile":
            active_ids = self.env.context.get("active_ids", [])
            moves = self.env["account.move"].browse(active_ids)
            move_lines = moves.mapped("line_ids")
            analytic_account = move_lines.mapped("analytic_account_id")
            analytic_tag = move_lines.mapped("analytic_tag_ids")
            taxes_account = (
                self.env["account.tax.repartition.line"]
                .search([("account_id", "!=", False)])
                .mapped("account_id")
            )
            moves_without_tax = move_lines.filtered(
                lambda l: l.account_id.user_type_id.type
                not in ("payable", "receivable")
                and l.account_id.id not in taxes_account.ids
            )
            default_tag = (
                all(line.analytic_tag_ids == analytic_tag for line in moves_without_tax)
                and analytic_tag
                or False
            )
            self.writeoff_analytic_account_id = (
                len(analytic_account) == 1 and analytic_account.id or False
            )
            self.writeoff_analytic_tag_ids = default_tag

    def _create_payment_vals_from_wizard(self):
        payment_vals = super()._create_payment_vals_from_wizard()
        if (
            not self.currency_id.is_zero(self.payment_difference)
            and self.payment_difference_handling == "reconcile"
        ):
            payment_vals["write_off_line_vals"][
                "analytic_account_id"
            ] = self.writeoff_analytic_account_id.id
            payment_vals["write_off_line_vals"][
                "analytic_tag_ids"
            ] = self.writeoff_analytic_tag_ids.ids
        return payment_vals
