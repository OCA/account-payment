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

from openerp.osv import orm


class account_voucher(orm.Model):
    _inherit = 'account.voucher'

    def __get_source(self, cr, uid, res, line_type, context=None):
        line_obj = self.pool.get('account.voucher.line')
        value = res.get('value')
        lines = value.get(line_type) if line_type in value else []

        for vals in lines:
            if vals.get('move_line_id'):
                vals['document_source'] = line_obj.get_document_source(
                    cr, uid, vals['move_line_id'], context=context
                )

    def recompute_voucher_lines(
        self, cr, uid, ids, partner_id, journal_id, price,
        currency_id, ttype, date, context=None
    ):

        res = super(account_voucher, self).recompute_voucher_lines(
            cr, uid, ids, partner_id, journal_id, price,
            currency_id, ttype, date, context=context
        )

        self.__get_source(cr, uid, res, 'line_cr_ids', context)
        self.__get_source(cr, uid, res, 'line_dr_ids', context)

        return res
