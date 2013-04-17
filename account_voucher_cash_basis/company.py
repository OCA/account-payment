# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011-2012 Domsense s.r.l. (<http://www.domsense.com>).
#    Copyright (C) 2012-2013 Agile Business Group sagl
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
from openerp.tools.translate import _

class res_company(orm.Model):
    _inherit = "res.company"
    _columns = {
        'vat_on_payment': fields.boolean('VAT on payment treatment'),
        'allow_distributing_write_off': fields.boolean('Allow distributing write-off', help="If not set, paying several 'cash basis' invoices with same voucher with write-off won't be allowed. If set, write-off will be distributed equally over invoices"),
        }
    
class account_config_settings(orm.TransientModel):
    _inherit = 'account.config.settings'
    _columns = {
        'vat_on_payment': fields.related(
            'company_id', 'vat_on_payment',
            type='boolean',
            string="VAT on payment treatment"),
        'allow_distributing_write_off': fields.related(
            'company_id', 'allow_distributing_write_off',
            type="boolean",
            string="Allow distributing write-off",
            help="If not set, paying several 'cash basis' invoices with same voucher with write-off won't be allowed. If set, write-off will be distributed equally over invoices"),
    }
    
    def onchange_company_id(self, cr, uid, ids, company_id, context=None):
        res = super(account_config_settings, self).onchange_company_id(cr, uid, ids, company_id, context=context)
        if company_id:
            company = self.pool.get('res.company').browse(cr, uid, company_id, context=context)
            res['value'].update({
                'vat_on_payment': company.vat_on_payment, 
                'allow_distributing_write_off': company.allow_distributing_write_off,
                })
        else: 
            res['value'].update({
                'vat_on_payment': False, 
                'allow_distributing_write_off': False,
                })
        return res
