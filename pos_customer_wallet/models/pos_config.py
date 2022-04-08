# Copyright 2022 Coop IT Easy SCRL fs
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class PosConfig(models.Model):
    _inherit = "pos.config"

    is_enabled_customer_wallet = fields.Boolean(
        string="Is Customer Wallet Enabled",
        compute="_compute_is_enabled_customer_wallet",
    )

    def _compute_is_enabled_customer_wallet(self):
        result = self.env["ir.config_parameter"].get_param(
            "account_customer_wallet.customer_wallet"
        )
        for pos_config in self:
            pos_config.is_enabled_customer_wallet = result
