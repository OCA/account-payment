# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class ResCompany(models.Model):

    _inherit = 'res.company'

    cash_discount_base_amount_type = fields.Selection(
        selection='_get_cash_discount_base_amount_types',
        required=True,
        default='untaxed',
    )

    @api.model
    def _get_cash_discount_base_amount_types(self):
        return [
            ('untaxed', _("Excluding tax")),
            ('total', _("Including all taxes")),
        ]
