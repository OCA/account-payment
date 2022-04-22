# Copyright 2022 Coop IT Easy SCRL fs
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class Company(models.Model):
    _inherit = "res.company"

    is_enabled_customer_wallet = fields.Boolean(
        compute="_compute_is_enabled_customer_wallet",
        string="Is Customer Wallet Enabled",
        store=True,
    )
    customer_wallet_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Customer Wallet Account",
    )

    @api.depends("customer_wallet_account_id")
    def _compute_is_enabled_customer_wallet(self):
        for company in self:
            company.is_enabled_customer_wallet = bool(
                company.customer_wallet_account_id
            )
