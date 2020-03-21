# Copyright (C) 2016-Today: La Louve (<http://www.lalouve.net/>)
# Copyright (C) 2019-Today: Druidoo (<https://www.druidoo.io>)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    property_payment_term_id = fields.Many2one(
        domain="[('for_customer', '=', True)]")

    property_supplier_payment_term_id = fields.Many2one(
        domain="[('for_supplier', '=', True)]")
