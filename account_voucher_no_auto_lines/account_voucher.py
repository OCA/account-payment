# -*- coding: utf-8 -*-
###############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2014 Savoir-faire Linux
#    (<http://www.savoirfairelinux.com>).
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
###############################################################################

from openerp.osv import orm

excluded_fields = ['move_line_id',
                   'amount',
                   'amount_unreconciled',
                   'account_id',
                   'date_original',
                   'name',
                   'date_due',
                   'type',
                   'amount_original',
                   'currency_id']

def copy_lines(cr, uid, ids, pool, context):
    if len(ids) == 0:
        return [], []

    line_ids = pool.search(cr, uid, [('voucher_id', '=', ids[0])],
                           context=context)
    saved_lines = pool.read(cr, uid, line_ids, excluded_fields, context=context)

    line_cr_ids = []
    line_dr_ids = []

    for line in saved_lines:
        del line['id']

        for key in ['currency_id', 'move_line_id', 'account_id']:
            if line[key]:
                line[key] = line[key][0]
            else:
                del line[key]

        if line.get('type') == 'cr':
            line_cr_ids.append(line)
        elif line.get('type') == 'dr':
            line_dr_ids.append(line)

    return line_cr_ids, line_dr_ids


class account_voucher(orm.Model):

    _inherit = 'account.voucher'

    def onchange_partner_id(self, cr, uid, ids, *args, **kwargs):

        res = super(account_voucher, self).onchange_partner_id(
            cr, uid, ids, *args, **kwargs)

        if 'value' in res and 'line_cr_ids' in res['value']:
            for line in res['value']['line_cr_ids']:
                line['amount'] = 0.0
                line['reconcile'] = False

        if 'value' in res and 'line_dr_ids' in res['value']:
            for line in res['value']['line_dr_ids']:
                line['amount'] = 0.0
                line['reconcile'] = False

        return res

    def onchange_amount(self, cr, uid, ids, *args, **kwargs):
        """
        Unsaved lines do not have ids and may look like this
        [5, False, {...}]

        Already saved lines should have an id defined
        [6, 455, ...]

        The third value is the data of the line. If the 
        value is False, then it means that the line didn't
        change.

        Reference to old ids can't be reused as the base class for
        voucher.line deletes references to old lines and replace them
        by "auto lines"... 
        """
        context = kwargs['context']

        line_pool = self.pool['account.voucher.line']
        line_cr_ids, line_dr_ids  = copy_lines(cr, uid, ids, line_pool, context)

        res = super(account_voucher, self).onchange_amount(
            cr, uid, ids, *args, **kwargs)

        res['value']['line_cr_ids'] = line_cr_ids
        res['value']['line_dr_ids'] = line_dr_ids

        return res
