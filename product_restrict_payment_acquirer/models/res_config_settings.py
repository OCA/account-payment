from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    product_acquirer_restriction_mode = fields.Selection(
        selection=[("first", "First Product"), ("all", "All Products")],
        config_parameter="product_acquirer_settings.product_acquirer_restriction_mode",
        default="first",
    )
