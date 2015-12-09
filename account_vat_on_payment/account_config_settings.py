# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Agile Business Group sagl (<http://www.agilebg.com>)
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


class AccountConfigSettings(orm.TransientModel):
    _inherit = 'account.config.settings'
    _columns = {
        'vat_on_payment': fields.related(
            'company_id', 'vat_on_payment',
            type='boolean',
            string="VAT on payment treatment",
            help="Company Selected applies VAT on payment."),
        'vat_payment_lines': fields.related(
            'company_id', 'vat_payment_lines',
            type='selection',
            selection=[('shadow_move', 'Move to Shadow Move'),
                       ('real_move', 'Keep on Real Move')],
            string='VAT lines on Payment',
            help="Selection field to configure if the account moves "
                 "generated on VAT on payment basis should modify the "
                 "implicit account moves generated normally, and to move "
                 "the partner account move line to the shadow move."),
        'vat_config_error': fields.related(
            'company_id', 'vat_config_error',
            type='selection',
            selection=[('raise_error', 'Raise Error'),
                       ('use_the_same', 'Use the same')],
            string='Miscconfiguration on VAT on Payment',
            help="Selection field to configure behaviour on missconfigured "
                 "datas on VAT on payment basis.\n"
                 " - 'Raise Error' is selected, if an account, journal "
                 "doesn't have set the corresponding VAT on payment "
                 "field, it will raise an error about missconfiguration.\n"
                 " - 'Use the same' is selected, it will not raise an error "
                 "about missconfiguration, and use the same account, journal "
                 "in VAT on payment."),
    }

    def onchange_company_id(self, cr, uid, ids, company_id, context=None):
        res = super(AccountConfigSettings, self).onchange_company_id(
            cr, uid, ids, company_id, context=context)
        if company_id:
            company = self.pool.get('res.company').browse(
                cr, uid, company_id, context=context)
            res['value'].update({
                'vat_on_payment': company.vat_on_payment,
                'vat_payment_lines': company.vat_payment_lines,
                'vat_config_error': company.vat_config_error,
            })
        else:
            res['value'].update({
                'vat_on_payment': False,
                'vat_payment_lines': 'shadow_move',
                'vat_config_error': 'raise_error',
            })
        return res

    def onchange_vat_payment_line(self, cr, uid, ids, vat_payment_lines,
                                  context=None):
        values = {}
        if vat_payment_lines:
            values.update({
                'vat_config_error': 'raise_error',
            })
        return {'value': values}
