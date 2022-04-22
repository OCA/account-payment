# Copyright 2022 Coop IT Easy SCRL fs
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class Partner(models.Model):
    _inherit = "res.partner"

    customer_wallet_account_id = fields.Many2one(
        comodel_name="account.account",
        related="company_id.customer_wallet_account_id",
        readonly=True,
    )
    customer_wallet_balance = fields.Monetary(
        string="Customer Wallet Balance",
        compute="_compute_customer_wallet_balance",
        readonly=True,
    )

    def _compute_customer_wallet_balance(self):
        for partner in self:
            move_lines = self.env["account.move.line"].search(
                [
                    ("account_id", "=", partner.customer_wallet_account_id.id),
                    ("partner_id", "=", partner.id),
                ]
            )

            balance = sum(-line.balance for line in move_lines)
            partner.customer_wallet_balance = balance
