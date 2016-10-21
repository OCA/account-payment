# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011-2012 Domsense s.r.l. (<http://www.domsense.com>).
#    Copyright (C) 2012-2014 Agile Business Group sagl
#    (<http://www.agilebg.com>)
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

from openerp.osv import fields, orm


class ResCompany(orm.Model):
    _inherit = "res.company"
    _columns = {
        'allow_distributing_write_off': fields.boolean(
            'Allow distributing write-off',
            help="If not set, paying several 'cash basis' invoices with same "
                 "voucher with write-off won't be allowed. If set, write-off "
                 "will be distributed equally over invoices"),
        'max_balance_diff': fields.integer(
            string="Max balancing precision in cash basis",
            help="In cash basis payments, while balancing "
            "unbalanced entries, this is "
            "maximum error allowed"
        ),
    }
    _defaults = {
        'max_balance_diff': 1
    }


class AccountConfigSettings(orm.TransientModel):
    _inherit = 'account.config.settings'
    _columns = {
        'allow_distributing_write_off': fields.related(
            'company_id', 'allow_distributing_write_off',
            type="boolean",
            string="Allow distributing write-off",
            help="If not set, paying several 'cash basis' invoices with same "
                 "voucher with write-off won't be allowed. If set, write-off "
                 "will be distributed equally over invoices"),
        'max_balance_diff': fields.related(
            'company_id', 'max_balance_diff',
            type="integer",
            string="Max balancing precision in cash basis",
            help="In cash basis payments, while balancing "
            "unbalanced entries, this is "
            "maximum error allowed"
        ),
    }

    def onchange_company_id(self, cr, uid, ids, company_id, context=None):
        res = super(AccountConfigSettings, self).onchange_company_id(
            cr, uid, ids, company_id, context=context)
        if company_id:
            company = self.pool.get('res.company').browse(
                cr, uid, company_id, context=context)
            res['value'].update({
                'allow_distributing_write_off': (
                    company.allow_distributing_write_off),
                'max_balance_diff': (
                    company.max_balance_diff),
            })
        else:
            res['value'].update({
                'allow_distributing_write_off': False,
                'max_balance_diff': False,
            })
        return res
