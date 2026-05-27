# Copyright 2022 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    account_payment_notification_automatic = fields.Selection(
        related="company_id.account_payment_notification_automatic",
        readonly=False,
    )
    account_payment_notification_method = fields.Selection(
        related="company_id.account_payment_notification_method", readonly=False
    )
    account_payment_notification_required = fields.Boolean(
        related="company_id.account_payment_notification_required", readonly=False
    )
