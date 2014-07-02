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

from openerp.osv import orm, fields


class res_partner(orm.Model):
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


class res_partner_bank(orm.Model):
    _inherit = 'res.partner.bank'

    def create(self, cr, uid, vals, context=None):
        if vals.get('default_bank') and vals.get('partner_id') and \
        vals.get('state'):
            sql = """UPDATE res_partner_bank SET
                    default_bank = '0'
                WHERE
                    partner_id = %i
                    AND default_bank = true
                    AND state='%s'""" % (vals['partner_id'], vals['state'])
            cr.execute(sql)
        return super(res_partner_bank, self).create(
            cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        if 'default_bank' in vals and vals['default_bank']:
            partner_bank = self.pool.get('res.partner.bank').browse(
                cr, uid, ids)[0]
            partner_id = partner_bank.partner_id.id
            if 'state' in vals and vals['state']:
                state = vals['state']
            else:
                state = partner_bank.state
            sql = """UPDATE res_partner_bank SET
                        default_bank='0'
                    WHERE
                        partner_id = %i
                        AND default_bank = true
                        AND state = '%s'
                        AND id <> %i""" % (partner_id, state, ids[0])
            cr.execute(sql)
        return super(res_partner_bank, self).write(
            cr, uid, ids, vals, context=context)

    _columns = {
        'default_bank': fields.boolean('Default'),
    }