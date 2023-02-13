from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    allowed_product_acquirer_ids = fields.Many2many(
        comodel_name="payment.acquirer",
        relation="product_acquirer_allowed_rel",
        column1="product_id",
        column2="acquirer_id",
        string="Allowed Acquirers",
        domain=[("state", "in", ["enabled", "test"])],
    )
