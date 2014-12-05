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

    def onchange_partner_id(self, cr, uid, ids, partner_id, remit_to,
                            journal_id, amount, currency_id,
                            ttype, date, context=None):
        journal_pool = self.pool.get('account.journal')
        rel_pool = self.pool.get('res.partner.relation')

        res = super(account_voucher, self).onchange_partner_id(
            cr, uid, ids, partner_id, journal_id, amount,
            currency_id, ttype, date, context=context)

        if partner_id and journal_id:
            journal = journal_pool.browse(cr, uid, journal_id, context=context)
            remit_rel_type = journal.company_id and \
                        journal.company_id.property_partner_rel_remit or False
            today = fields.date.context_today(self,cr,uid,context=context)
            remit_rel_ids = rel_pool.search(cr, uid,
                            [('left_partner_id', '=', partner_id),
                             ('type_id', '=', remit_rel_type.id),
                             '|', ('date_start', '<=', today),
                             ('date_start', '=', False),
                             '|',
                             ('date_end', '>=', today),
                             ('date_end', '=', False)])
            if remit_rel_ids:
                remit_rel = rel_pool.browse(cr, uid, remit_rel_ids[0],
                                            context=context)
                res['value']['remit_to'] = remit_rel.right_partner_id.id
            else:
                res['value']['remit_to'] = partner_id

        return res