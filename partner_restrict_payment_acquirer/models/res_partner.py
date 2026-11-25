from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    allowed_payment_provider_ids = fields.Many2many(
        comodel_name="payment.provider",
        relation="partner_allowed_payment_provider_rel",
        column1="partner_id",
        column2="payment_provider_id",
        string="Allowed Payment Providers",
        domain=[("state", "in", ["enabled", "test"])],
    )
