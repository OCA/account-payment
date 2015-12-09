# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011-2012 Domsense s.r.l. (<http://www.domsense.com>).
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


class ResCompany(orm.Model):
    _inherit = "res.company"
    _columns = {
        'vat_on_payment': fields.boolean(
            'VAT on payment treatment',
            help="Company Selected applies VAT on payment."),
        'vat_payment_lines': fields.selection(
            [('shadow_move', 'Move to Shadow Move'),
             ('real_move', 'Keep on Real Move')],
            'VAT lines on Payment',
            default='shadow_move',
            help="Selection field to configure if the account moves "
                 "generated on VAT on payment basis should modify the "
                 "implicit account moves generated normally, and to move "
                 "the partner account move line to the shadow move."),
        'vat_config_error': fields.selection(
            [('raise_error', 'Raise Error'),
             ('use_the_same', 'Use the same')],
            'Miscconfiguration on VAT on Payment',
            default='raise_error',
            help="Selection field to configure behaviour on missconfigured "
                 "datas on VAT on payment basis.\n"
                 " - 'Raise Error' is selected, if an account, journal "
                 "doesn't have set the corresponding VAT on payment "
                 "field, it will raise an error about missconfiguration.\n"
                 " - 'Use the same' is selected, it will not raise an error "
                 "about missconfiguration, and use the same account, journal "
                 "in VAT on payment.")
            
    }
