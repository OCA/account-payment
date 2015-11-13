# -*- coding: utf-8 -*-
# © 2015 Eficent
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp.osv import orm


class AccountInvoice(orm.Model):
    _inherit = 'account.invoice'

    def invoice_pay_customer(self, cr, uid, ids, context=None):
        res = super(AccountInvoice, self).invoice_pay_customer(
            cr, uid, ids, context=context)
        if res and ids:
            inv = self.browse(cr, uid, ids[0], context=context)
            addr = self.pool.get('res.partner').address_get(
                cr, uid, [inv.partner_id.id], ['remit_to'])
            if addr and 'remit_to' in addr:
                res['context']['remit_to'] = addr['remit_to']
            else:
                res['context']['remit_to'] = inv.partner_id.id
        return res
