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

from openerp.osv import orm, fields


class account_voucher(orm.Model):

    _inherit = 'account.voucher'

    def onchange_amount(self, *args, **kwargs):

        res = super(account_voucher, self).onchange_amount(*args, **kwargs)

        if 'context' in kwargs and 'type' in kwargs['context']:
            if kwargs['context']['type'] == 'receipt':
                lines = res['value']['line_cr_ids']
            elif kwargs['context']['type'] == 'payment':
                lines = res['value']['line_dr_ids']

            for line in lines:
                line['amount'] = 0.0

        return res
