# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2008 Zikzakmedia S.L. (http://zikzakmedia.com)
#                       Jordi Esteve <jesteve@zikzakmedia.com>
#
#    Copyright (C) 2011 Domsense srl (<http://www.domsense.com>)
#    Copyright (C) 2011-2013 Agile Business Group sagl
#    (<http://www.agilebg.com>)
#    Ported to Odoo by Andrea Cometa <info@andreacometa.it>
#    Ported to v8 API by Eneko Lacunza <elacunza@binovo.es>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.tools.translate import _
from openerp import models, fields, api
from openerp.osv import orm


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    invoice_origin = fields.Char(related='invoice.origin', string='Source Doc')
    invoice_date = fields.Date(related='invoice.date_invoice',
                               string='Invoice Date')
    partner_ref = fields.Char(related='partner_id.ref', string='Partner Ref')
    payment_term_id = fields.Many2one('account.payment.term',
                                      related='invoice.payment_term',
                                      string='Payment Terms')
    stored_invoice_id = fields.Many2one('account.invoice',
                                        compute='_get_invoice',
                                        string='Invoice', store=True)

    @api.depends('move_id', 'invoice.move_id')
    def _get_invoice(self):
        for line in self:
            inv_ids = self.env['account.invoice'].search(
                [('move_id', '=', line.move_id.id)])
            if len(inv_ids) > 1:
                raise orm.except_orm(
                    _('Error'),
                    _('Inconsistent data: move %s has more than one invoice')
                    % line.move_id.name)
            if line.invoice:
                line.stored_invoice_id = inv_ids[0]
            else:
                line.stored_invoice_id = False

    day = fields.Char(compute='_get_day', string='Day', size=16, store=True)

    @api.depends('date_maturity')
    def _get_day(self):
        for line in self:
            if line.date_maturity:
                line.day = line.date_maturity
            else:
                line.day = False

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        model_data_obj = self.env['ir.model.data']
        ids = model_data_obj.search([
            ('module', '=', 'account_due_list'),
            ('name', '=', 'view_payments_tree')])
        if ids:
            view_payments_tree_id = model_data_obj.get_object_reference(
                'account_due_list', 'view_payments_tree')
        if ids and view_id == view_payments_tree_id[1]:
            # Use due list
            result = super(models.Model, self).fields_view_get(
                view_id, view_type, toolbar=toolbar, submenu=submenu)
        else:
            # Use special views for account.move.line object
            # (for ex. tree view contains user defined fields)
            result = super(AccountMoveLine, self).fields_view_get(
                view_id, view_type, toolbar=toolbar, submenu=submenu)
        return result
