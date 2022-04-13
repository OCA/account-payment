# Copyright 2022 Coop IT Easy SCRL fs
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class Partner(models.Model):
    _inherit = "res.partner"

    # TODO: What if this setting is changed during runtime? Does res.partner
    # detect the change?
    customer_wallet_account_id = fields.Many2one(
        comodel_name="account.account",
        compute="_compute_customer_wallet_account_id",
    )
    # TODO: Is Monetary the correct field? What is behaviour with multiple
    # currencies?
    customer_wallet_balance = fields.Monetary(
        string="Customer Wallet Balance",
        currency_field="company_currency_id",
        compute="_compute_customer_wallet_balance",
        readonly=True,
    )
    company_currency_id = fields.Many2one(
        comodel_name="res.currency",
        related="company_id.currency_id",
        string="Company Currency",
        help="Utility field to express amount currency",
        readonly=True,
        store=True,
    )

    def _compute_customer_wallet_account_id(self):
        account_id = self.env["ir.config_parameter"].get_param(
            "account_customer_wallet.customer_wallet_account_id"
        )
        result = self.env["account.account"].browse(int(account_id))
        for partner in self:
            partner.customer_wallet_account_id = result

    @api.depends("customer_wallet_account_id.move_line_ids")
    def _compute_customer_wallet_balance(self):
        for partner in self:
            # TODO: Use filtered or search?
            move_lines = partner.customer_wallet_account_id.move_line_ids.filtered(
                lambda line: line.partner_id == partner
            )
            # move_lines = self.env["account.move.line"].search([
            #     ("account_id", "=", partner.customer_wallet_account_id.id),
            #     ("partner_id", "=", partner.id),
            # ])

            # TODO: Is this correct?
            balance = sum(-line.balance for line in move_lines)
            partner.customer_wallet_balance = balance
