# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011-2012 Domsense s.r.l. (<http://www.domsense.com>).
#    Copyright (C) 2014 Agile Business Group sagl (<http://www.agilebg.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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

from openerp.osv import orm, fields
from openerp.tools.translate import _
from openerp import api


class AccountInvoice(orm.Model):

    def _get_vat_on_payment(self, cr, uid, context=None):
        return self.pool.get('res.users').browse(
            cr, uid, uid, context).company_id.vat_on_payment

    def _set_vat_on_payment_account(self, cr, uid, line_tuple, context=None):
        acc_pool = self.pool.get('account.account')
        account = acc_pool.browse(
            cr, uid, line_tuple[2]['account_id'], context=context)
        if account.type not in ['receivable', 'payable']:
            if not account.vat_on_payment_related_account_id:
                raise orm.except_orm(
                    _('Error'),
                    _("The invoice is 'VAT on payment' but "
                      "account %s does not have a related shadow "
                      "account")
                    % account.name)
            line_tuple[2]['real_account_id'] = line_tuple[
                2]['account_id']
            line_tuple[2]['account_id'] = (
                account.vat_on_payment_related_account_id.id)
        return line_tuple

    def _set_vat_on_payment_tax_code(self, cr, uid, line_tuple, context=None):
        tax_code_pool = self.pool.get('account.tax.code')
        tax_code = tax_code_pool.browse(
            cr, uid, line_tuple[2]['tax_code_id'], context=context)
        if not tax_code.vat_on_payment_related_tax_code_id:
            raise orm.except_orm(
                _('Error'),
                _("The invoice is 'VAT on payment' but "
                  "tax code %s does not have a related shadow "
                  "tax code")
                % tax_code.name)
        line_tuple[2]['real_tax_code_id'] = line_tuple[
            2]['tax_code_id']
        line_tuple[2]['tax_code_id'] = (
            tax_code.vat_on_payment_related_tax_code_id.id)
        return line_tuple

    def finalize_invoice_move_lines(self, cr, uid, ids, move_lines, context):
        """
        Use shadow accounts for journal entry to be generated, according to
        account and tax code related records
        """
        move_lines = super(AccountInvoice, self).finalize_invoice_move_lines(
            cr, uid, ids, move_lines, context)
        assert len(ids) == 1
        invoice_browse = self.browse(cr, uid, ids, context=context)
        context = self.pool['res.users'].context_get(cr, uid)
        new_move_lines = []
        for line_tuple in move_lines:
            if invoice_browse.vat_on_payment:
                if line_tuple[2].get('account_id', False):
                    line_tuple = self._set_vat_on_payment_account(
                        cr, uid, line_tuple, context=context)
                if line_tuple[2].get('tax_code_id', False):
                    line_tuple = self._set_vat_on_payment_tax_code(
                        cr, uid, line_tuple, context=context)
            new_move_lines.append(line_tuple)
        return new_move_lines

    @api.cr_uid_ids
    def onchange_partner_id(
            self, cr, uid, ids, inv_type, partner_id, date_invoice=False,
            payment_term=False, partner_bank_id=False, company_id=False,
            context=False):
        res = super(AccountInvoice, self).onchange_partner_id(
            cr, uid, ids, inv_type, partner_id, date_invoice, payment_term,
            partner_bank_id, company_id, context)
        # default value for VAT on Payment is changed every time the
        # customer/supplier is changed
        partner_obj = self.pool.get("res.partner")
        context = self.pool['res.users'].context_get(cr, uid)
        if partner_id:
            p = partner_obj.browse(cr, uid, partner_id, context=context)
            if p.property_account_position:
                res['value'][
                    'vat_on_payment'
                ] = p.property_account_position.default_has_vat_on_payment
        return res

    _inherit = "account.invoice"
    _columns = {
        'vat_on_payment': fields.boolean('Vat on payment'),
    }
    _defaults = {
        'vat_on_payment': _get_vat_on_payment,
    }
