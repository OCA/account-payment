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

    def basic_onchange_partner(self, cr, uid, ids, partner_id,
                               journal_id, ttype, context=None):
        res = super(account_voucher, self).basic_onchange_partner(
            cr, uid, ids, partner_id, journal_id, ttype, context=context)
        partner_pool = self.pool.get('res.partner')
        partner = partner_pool.browse(cr, uid, partner_id, context=context)
        ttype = context.get('type', 'bank')
        if ttype == 'payment' \
                and partner.supplier_payment_method:
            res['value']['journal_id'] = \
                partner.supplier_payment_method.id
        elif ttype == 'receipt' \
                and partner.customer_payment_method:
            res['value']['journal_id'] = \
                partner.customer_payment_method.id
        return res
