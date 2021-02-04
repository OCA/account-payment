# Copyright 2019 Open Source Integrators (http://www.opensourceintegrators.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_exclude_shipping_amount = fields.Boolean(
        string="Exclude Shippling Amount",
        help="Check this box if want to exclude shipping charges from discount",
    )
