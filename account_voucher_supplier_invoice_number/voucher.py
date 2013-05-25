# -*- coding: utf-8 -*-
##############################################################################
#    
#    Copyright (C) 2013 Agile Business Group sagl
#    (<http://www.agilebg.com>)
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

from openerp.osv import fields, orm
from tools.translate import _

class voucher_line(orm.Model):
    _inherit = 'account.voucher.line'
    
    def get_suppl_inv_num(self, cr, uid, move_line_id, context=None):
        move_line = self.pool.get('account.move.line').browse(cr, uid, move_line_id, context)
        return (move_line.invoice and move_line.invoice.supplier_invoice_number or '')
    
    def _get_supplier_invoice_number(self, cr, uid, ids, name, args, context=None):
        res={}
        for line in self.browse(cr, uid, ids, context):
            res[line.id] = ''
            if line.move_line_id:
                res[line.id] = self.get_suppl_inv_num(cr, uid,
                    line.move_line_id.id, context=context)
        return res
    
    _columns = {
        'supplier_invoice_number': fields.function(_get_supplier_invoice_number,
            type='char', size=64, string="Supplier Invoice Number"),
        }

class voucher(orm.Model):
    _inherit = 'account.voucher'
    
    def recompute_voucher_lines(self, cr, uid, ids, partner_id, journal_id, price,
        currency_id, ttype, date, context=None):
        res = super(voucher,self).recompute_voucher_lines(cr, uid, ids, partner_id,
            journal_id, price,
            currency_id, ttype, date, context=context)
        line_obj = self.pool.get('account.voucher.line')
        if res.get('value') and res['value'].get('line_cr_ids'):
            for vals in res['value']['line_cr_ids']:
                if vals.get('move_line_id'):
                    vals['supplier_invoice_number'] = line_obj.get_suppl_inv_num(
                        cr, uid, vals['move_line_id'], context=context)
        if res.get('value') and res['value'].get('line_dr_ids'):
            for vals in res['value']['line_dr_ids']:
                if vals.get('move_line_id'):
                    vals['supplier_invoice_number'] = line_obj.get_suppl_inv_num(
                        cr, uid, vals['move_line_id'], context=context)
        return res
