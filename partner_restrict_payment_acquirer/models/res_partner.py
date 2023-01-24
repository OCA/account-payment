from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    allowed_acquirer_ids = fields.Many2many(
        comodel_name="payment.acquirer",
        relation="partner_acquirere_allowed_rel",
        column1="partner_id",
        columnt2="acquirer_id",
        string="Allowed Acquirers",
        domain=[("state", "in", ["enabled", "test"])],
    )
