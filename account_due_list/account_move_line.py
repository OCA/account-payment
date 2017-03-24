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

from odoo.tools.translate import _
from odoo import models, fields, api
from odoo.osv import orm


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    invoice_origin = fields.Char(
        related='invoice_id.origin',
        string='Source Doc'
    )
    invoice_date = fields.Date(related='invoice_id.date_invoice',
                               string='Invoice Date')
    partner_ref = fields.Char(related='partner_id.ref', string='Partner Ref')
    payment_term_id = fields.Many2one('account.payment.term',
                                      related='invoice_id.payment_term_id',
                                      string='Payment Terms')
    stored_invoice_id = fields.Many2one('account.invoice',
                                        compute='_get_invoice',
                                        string='Invoice', store=True)

    maturity_residual = fields.Float(
        compute='_maturity_residual', string="Residual Amount", store=True,
        help="The residual amount on a receivable or payable of a journal "
             "entry expressed in the company currency.")

    @api.multi
    # @api.depends('date_maturity', 'debit', 'credit', 'reconcile_id',
    #              'reconcile_partial_id', 'account_id.reconcile',
    #              'amount_currency', 'reconcile_partial_id.line_partial_ids',
    #              'currency_id', 'company_id.currency_id')
    @api.depends('date_maturity', 'debit', 'credit',
                 'full_reconcile_id',
                 'amount_currency',
                 'currency_id', 'company_id.currency_id')
    def _maturity_residual(self):
        """
            inspired by amount_residual
        """
        for move_line in self:
            sign = (move_line.debit - move_line.credit) < 0 and -1 or 1
            move_line.maturity_residual = move_line.amount_residual * sign

    @api.depends('move_id', 'invoice_id.move_id')
    def _get_invoice(self):
        for line in self:
            inv_ids = self.env['account.invoice'].search(
                [('move_id', '=', line.move_id.id)])
            if len(inv_ids) > 1:
                raise orm.except_orm(
                    _('Error'),
                    _('Inconsistent data: move %s has more than one invoice')
                    % line.move_id.name)
            if line.invoice_id:
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
