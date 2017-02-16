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
from openerp.osv import orm, fields


class res_partner(orm.Model):
    _inherit = "res.partner"

    _columns = {
        'customer_payment_method': fields.property(
            'account.journal', type='many2one', relation='account.journal',
            string='Customer Payment Method', view_load=True,
            help="Select the default payment method for this customer."),
        'supplier_payment_method': fields.property(
            'account.journal', type='many2one', relation='account.journal',
            string='Customer Payment Method', view_load=True,
            help="Select the default payment method for this supplier."),

    }

    def _commercial_fields(self, cr, uid, context=None):
        res = super(res_partner, self)._commercial_fields(
            cr, uid, context=context)
        res += ['supplier_payment_method', 'customer_payment_method']
        return res
