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

        context = kwargs.get('context', None)

        line_pool = self.pool.get('account.voucher.line')

        def copy_lines():
            if len(ids) == 0:
                return [], []

            line_ids = line_pool.search(cr, uid, [('voucher_id', '=', ids[0])])
            saved_lines = line_pool.read(cr, uid, line_ids)

            line_cr_ids = []
            line_dr_ids = []

            for line in saved_lines:
                for key in ['id','reconcile', 'supplier_invoice_number',
                            'untax_amount', 'company_id',
                            'account_analytic_id', 'voucher_id',
                            'partner_id']:
                    del line[key]

                line['currency_id'] = line['currency_id'][0]
                line['move_line_id'] = line['move_line_id'][0]
                line['account_id'] = line['account_id'][0]

                if line.get('type') == 'cr':
                    line_cr_ids.append(line)
                else:
                    line_dr_ids.append(line)


            return line_cr_ids, line_dr_ids


        if context:
            line_cr_ids, line_dr_ids  = copy_lines()

        res = super(account_voucher, self).onchange_amount(
            cr, uid, ids, *args, **kwargs)


        if context:
            res['value']['line_cr_ids'] = line_cr_ids
            res['value']['line_dr_ids'] = line_dr_ids

        return res
