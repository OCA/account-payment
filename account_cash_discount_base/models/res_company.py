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
    cash_discount_use_tax_adjustment = fields.Boolean(
        compute='_compute_cash_discount_tax_adjustment',
        store=True,
    )

    @api.model
    def _get_cash_discount_base_amount_types(self):
        return [
            ('untaxed', _("Excluding tax")),
            ('total', _("Including all taxes")),
        ]

    @api.multi
    @api.depends(
        'cash_discount_base_amount_type',
    )
    def _compute_cash_discount_tax_adjustment(self):
        for rec in self:
            rec.cash_discount_use_tax_adjustment = (
                rec.cash_discount_base_amount_type == 'total'
            )
