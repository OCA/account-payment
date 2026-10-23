from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    payment_line_restrict_counterpart_partner = fields.Boolean(
        related="company_id.payment_line_restrict_counterpart_partner",
        readonly=False,
    )
