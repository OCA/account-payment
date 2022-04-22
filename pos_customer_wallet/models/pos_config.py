# Copyright 2022 Coop IT Easy SCRL fs
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class PosConfig(models.Model):
    _inherit = "pos.config"

    is_enabled_customer_wallet = fields.Boolean(
        related="company_id.is_enabled_customer_wallet",
        string="Is Customer Wallet Enabled",
    )
