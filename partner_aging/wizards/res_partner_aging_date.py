# -*- coding: utf-8 -*-
# Copyright 2017 Ursa Information Systems <http://www.ursainfosystems.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class ResPartnerAgingDate(models.TransientModel):
    _name = "res.partner.aging.date"

    age_date = fields.Datetime("Aging Date",
                               required=True,
                               default=lambda self: fields.Datetime.now())

    @api.multi
    def open_customer_aging(self):
        ctx = self._context.copy()
        ctx.update({'age_date': self.age_date})

        customer_aging = self.env['res.partner.aging.customer']
        customer_aging.execute_aging_query(age_date=self.age_date)

        return {
            'name': _('Customer Aging'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'res.partner.aging.customer',
            'type': 'ir.actions.act_window',
            'domain': [('total', '!=', 0)],
            'context': ctx,
        }

    @api.multi
    def open_supplier_aging(self):
        ctx = self._context.copy()
        ctx.update({'age_date': self.age_date})

        supplier_aging = self.env['res.partner.aging.supplier']
        supplier_aging.execute_aging_query(age_date=self.age_date)

        return {
            'name': _('Supplier Aging'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'res.partner.aging.supplier',
            'type': 'ir.actions.act_window',
            'domain': [('total', '!=', 0)],
            'context': ctx,
        }
