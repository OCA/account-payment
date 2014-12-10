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

    def invoice_pay_customer(self, cr, uid, ids, context=None):
        res = super(account_invoice, self).invoice_pay_customer(
            cr, uid, ids, context=context)
        if res and ids:
            inv = self.browse(cr, uid, ids[0], context=context)
            if inv.type in ('in_invoice', 'in_refund') \
                    and inv.partner_id.supplier_payment_method:
                res['context']['default_journal_id'] = \
                    inv.partner_id.supplier_payment_method.id or False
            elif inv.type in ('out_invoice', 'out_refund') \
                    and inv.partner_id.customer_payment_method:
                res['context']['default_journal_id'] = \
                    inv.partner_id.customer_payment_method.id or False
        return res