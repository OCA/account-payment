# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import fields, models


class PaymentIcon(models.Model):
    _inherit = "payment.icon"

    worldline_code = fields.Char()

    def _get_from_wordline_code(self, code, mapping=None):
        generic_to_specific_mapping = mapping or {}
        specific_to_generic_mapping = {
            v: k for k, v in generic_to_specific_mapping.items()
        }
        return self.search(
            [("worldline_code", "=", specific_to_generic_mapping.get(code, code))],
            limit=1,
        )
