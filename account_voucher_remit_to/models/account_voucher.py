# -*- coding: utf-8 -*-
# © 2015 Eficent
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp.osv import fields, orm


class AccountVoucher(orm.Model):
    _inherit = 'account.voucher'

    _columns = {
        'remit_to': fields.many2one('res.partner', 'Remit-to address',
                                    change_default=1, readonly=True,
                                    states={'draft': [('readonly', False)]}),
    }

    _defaults = {
        'remit_to':
            lambda self, cr, uid, context:
            context.get('partner_id', False) and self.pool.get(
                'res.partner').address_get(
                cr, uid, [context['partner_id']], ['remit_to'])['remit_to'],
    }

    def onchange_partner_id(self, cr, uid, ids, partner_id,
                            journal_id, amount, currency_id,
                            ttype, date, context=None):

        res = super(AccountVoucher, self).onchange_partner_id(
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
