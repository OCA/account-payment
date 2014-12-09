# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Eficent (<http://www.eficent.com/>)
#              Jordi Ballester Alomar <jordi.ballester@eficent.com>
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
from openerp.osv import fields, osv


class account_voucher(osv.osv):
    _inherit = 'account.voucher'

    _columns = {
        'remit_to': fields.many2one('res.partner', 'Remit-to address',
                                    change_default=1, readonly=True,
                                    states={'draft': [('readonly', False)]}),
    }

    _defaults = {
        'remit_to':
            lambda self, cr, uid, context:
            context.get('partner_id', False)
            and self.pool.get('res.partner').address_get(
                cr, uid, [context['partner_id']], ['remit_to'])['remit_to'],
    }

    def onchange_partner_id(self, cr, uid, ids, partner_id,
                            journal_id, amount, currency_id,
                            ttype, date, context=None):

        res = super(account_voucher, self).onchange_partner_id(
            cr, uid, ids, partner_id, journal_id, amount,
            currency_id, ttype, date, context=context)
        if not res:
            return res

        if not partner_id:
            res['value']['remit_to'] = False
            return res

        addr = self.pool.get('res.partner').address_get(
            cr, uid, [partner_id], ['remit_to'])

        if addr and 'remit_to' in addr:
            res['value']['remit_to'] = addr['remit_to']
        else:
            res['value']['remit_to'] = partner_id
        return res