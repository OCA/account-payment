from odoo import api, models


class PaymentProvider(models.Model):
    _inherit = "payment.provider"

    @api.model
    def _get_compatible_providers(self, company_id, partner_id, amount, **kwargs):
        providers = super()._get_compatible_providers(
            company_id, partner_id, amount, **kwargs
        )
        customer_providers = (
            self.env["res.partner"].browse(partner_id).allowed_payment_provider_ids
        )
        if customer_providers:
            return providers & customer_providers
        return providers
