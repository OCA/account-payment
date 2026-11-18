# Copyright 2024 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    days_not_pay = fields.Boolean(
        config_parameter="account_payment_term_partner_not_paydays.days_not_pay"
    )

    def set_values(self):
        res = super().set_values()
        # Both fields read the parameter without any dependency to follow.
        self.env["res.partner"].invalidate_model(["days_not_pay"])
        self.env["account.move"].invalidate_model(["message_range_not_pay"])
        return res
