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

        res = super(account_voucher, self).onchange_amount(
            cr, uid, ids, *args, **kwargs)

        if 'context' in kwargs and 'line_cr_ids' in kwargs['context']:
            res['value']['line_cr_ids'] = kwargs['context']['line_cr_ids']

        if 'context' in kwargs and 'line_dr_ids' in kwargs['context']:
            res['value']['line_dr_ids'] = kwargs['context']['line_dr_ids']

        return res
