# Copyright 2022 Coop IT Easy SCRL fs
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    account_customer_wallet = fields.Boolean(
        string="Account Customer Wallet",
        config_parameter="account_customer_wallet.account_customer_wallet",
        help="Let customers pay from a wallet account",
    )
    customer_wallet_journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Customer Wallet Journal",
        required=True,
    )
