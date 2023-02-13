from odoo import api, fields, models


class ProductAcquirerSettings(models.TransientModel):
    _inherit = "res.config.settings"

    product_acquirer_restriction_mode = fields.Selection(
        selection=[
            ("first", "First Product"),
            ("all", "All Products"),
        ]
    )

    def set_values(self):
        result = super(ProductAcquirerSettings, self).set_values()
        self.env["ir.config_parameter"].set_param(
            "product_acquirer_settings.product_acquirer_restriction_mode",
            self.product_acquirer_restriction_mode,
        )
        return result

    @api.model
    def get_values(self):
        result = self.env["ir.config_parameter"].get_param(
            "product_acquirer_settings.product_acquirer_restriction_mode"
        )
        return {"product_acquirer_restriction_mode": result}
