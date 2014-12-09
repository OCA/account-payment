# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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


class account_invoice(orm.Model):
    _inherit = 'account.invoice'

    _columns = {
        'payment_method_id': fields.many2one(
            'account.journal', 'Payment Method',
            help="Payment method used in Payment vouchers."),
    }

    def onchange_partner_id(
            self, cr, uid, ids, type, partner_id, date_invoice=False,
            payment_term=False, partner_bank_id=False, company_id=False):
        res = super(account_invoice, self).onchange_partner_id(
            cr, uid, ids, type, partner_id, date_invoice=date_invoice,
            payment_term=payment_term, partner_bank_id=partner_bank_id,
            company_id=company_id)
        if partner_id:
            partner = self.pool['res.partner'].browse(cr, uid, partner_id)
            if type in ('in_invoice', 'in_refund'):
                res['value']['payment_method_id'] = \
                    partner.supplier_payment_method.id or False
            elif type in ('out_invoice', 'out_refund'):
                res['value'].update({
                    'payment_method_id':
                    partner.customer_payment_method.id or False,
                })
        else:
            res['value']['payment_method_id'] = False
        return res

    def invoice_pay_customer(self, cr, uid, ids, context=None):
        res = super(account_invoice, self).invoice_pay_customer(
            cr, uid, ids, context=context)
        if res and ids:
            inv = self.browse(cr, uid, ids[0], context=context)
            if inv.payment_method_id:
                res['default_type'] = inv.payment_method_id
                res['type'] = res['default_type']
        return res