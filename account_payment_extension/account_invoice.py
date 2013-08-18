# -*- encoding: utf-8 -*-
##############################################################################
#
# OpenERP, Open Source Management Solution
# Copyright (c) 2008 Zikzakmedia S.L. (http://zikzakmedia.com)
#                    All Rights Reserved.Jordi Esteve <jesteve@zikzakmedia.com>
# AvanzOSC, Avanzed Open Source Consulting
# Copyright (C) 2011-2012 Iker Coranti (www.avanzosc.com). All Rights Reserved
# Copyright (C) 2013 Akretion Ltda ME (www.akretion.com) All Rights Reserved
# Renato Lima <renato.lima@akretion.com.br>
# $Id$
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, orm


class account_invoice(orm.Model):
    _inherit = 'account.invoice'
    _columns = {
        'payment_type': fields.many2one('payment.type', 'Payment type'),
    }

    def onchange_partner_id(self, cr, uid, ids, type, partner_id,
                            date_invoice=False, payment_term=False,
                            partner_bank_id=False, company_id=False):

        result = super(account_invoice, self).onchange_partner_id(
            cr, uid, ids, type, partner_id, date_invoice, payment_term,
            partner_bank_id, company_id)
        payment_type = False
        if partner_id:
            partner = self.pool.get('res.partner').browse(cr, uid, partner_id)
            if type in ('in_invoice', 'in_refund'):
                payment_type = partner.payment_type_supplier.id
            else:
                payment_type = partner.payment_type_customer.id
            result['value']['payment_type'] = payment_type
        return self.onchange_payment_type(
            cr, uid, ids, payment_type, partner_id, result)

    def onchange_payment_type(self, cr, uid, ids, payment_type,
                            partner_id, result=None):
        if not result:
            result = {'value': {}}

        if payment_type and partner_id:
            bank_types = self.pool.get('payment.type').browse(
                cr, uid, payment_type).suitable_bank_types
            # If the payment type is related with a bank account
            if bank_types:
                bank_types = [bt.code for bt in bank_types]
                partner_bank_obj = self.pool.get('res.partner.bank')
                args = [('partner_id', '=', partner_id),
                    ('default_bank', '=', 1),
                    ('state', 'in', bank_types)]
                bank_account_id = partner_bank_obj.search(cr, uid, args)
                if bank_account_id:
                    result['value']['partner_bank_id'] = bank_account_id[0]
                    return result
        result['value']['partner_bank_id'] = False
        return result

    def action_move_create(self, cr, uid, ids, context=None):
        result = super(account_invoice, self).action_move_create(
            cr, uid, ids, context)
        if result:
            for inv in self.browse(cr, uid, ids, context):
                move_line_ids = []
                for move_line in inv.move_id.line_id:
                    if (move_line.account_id.type == 'receivable' or
                    move_line.account_id.type == 'payable') and \
                    move_line.state != 'reconciled' and \
                    not move_line.reconcile_id.id:
                        move_line_ids.append(move_line.id)
                if len(move_line_ids) and inv.partner_bank_id:
                    aml_obj = self.pool.get("account.move.line")
                    aml_obj.write(cr, uid, move_line_ids,
                        {'partner_bank_id': inv.partner_bank_id.id})
        return result
