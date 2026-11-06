from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    account_payment_notification_domain = fields.Char(
        related="company_id.account_payment_notification_domain",
        readonly=False,
    )
    account_payment_notification_start_date = fields.Date(
        related="company_id.account_payment_notification_start_date",
        readonly=False,
    )
