# Copyright 2022 Coop IT Easy SCRL fs
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    customer_wallet_account_id = fields.Many2one(
        comodel_name="account.account",
        related="company_id.customer_wallet_account_id",
        readonly=False,
        string="Customer Wallet Account",
        help="The account where all wallet transactions will be recorded",
    )
