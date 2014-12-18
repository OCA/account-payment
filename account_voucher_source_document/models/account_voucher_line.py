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


class account_voucher_line(orm.Model):
    _inherit = 'account.voucher.line'

    def get_document_source(self, cr, uid, move_line_id, context=None):
        line_pool = self.pool.get('account.move.line')
        move_line = line_pool.browse(cr, uid, move_line_id, context)

        return (
            move_line.invoice
            and move_line.invoice.origin
            or ''
        )

    def _get_supplier_invoice_number(
            self, cr, uid, ids, name, args, context=None):

        res = {}
        for line in self.browse(cr, uid, ids, context):
            res[line.id] = ''
            if line.move_line_id:
                res[line.id] = self.get_document_source(
                    cr, uid, line.move_line_id.id, context=context
                )

        return res

    _columns = {
        'document_source': fields.function(
            _get_supplier_invoice_number,
            type='char',
            size=64,
            string="Document source"
        ),
    }
