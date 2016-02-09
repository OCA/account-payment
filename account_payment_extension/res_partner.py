# -*- encoding: utf-8 -*-
#
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
#

from openerp.osv import orm, fields


class ResPartner(orm.Model):
    _inherit = 'res.partner'
    _columns = {
        'payment_type_customer': fields.property(
            'payment.type', type='many2one', relation='payment.type',
            string='Customer Payment Type', method=True, view_load=True,
            help="Payment type of the customer"),
        'payment_type_supplier': fields.property(
            'payment.type', type='many2one', relation='payment.type',
            string='Supplier Payment Type', method=True, view_load=True,
            help="Payment type of the supplier"),
    }


class ResPartnerBank(orm.Model):
    _inherit = 'res.partner.bank'

    def _unmark_default(self, cr, uid, bank_id, partner_id, state):
        bank_ids = self.search(
            cr, uid, [('default_bank', '=', True), ('id', '!=', bank_id),
                      ('state', '=', state), ('partner_id', '=', partner_id)])
        self.write(cr, uid, bank_ids, {'default_bank': False})

    def create(self, cr, uid, vals, context=None):
        if vals.get('default_bank') and vals.get('partner_id') and \
                vals.get('state'):
            self._unmark_default(
                cr, uid, False, vals['partner_id'], vals['state'])
        return super(ResPartnerBank, self).create(
            cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        if vals.get('default_bank'):
            partner_bank = self.browse(cr, uid, ids[0])
            partner_id = vals.get('partner_id') or partner_bank.partner_id.id
            state = vals.get('state') or partner_bank.state
            self._unmark_default(cr, uid, False, partner_id, state)
        return super(ResPartnerBank, self).write(
            cr, uid, ids, vals, context=context)

    _columns = {
        'default_bank': fields.boolean('Default'),
    }
