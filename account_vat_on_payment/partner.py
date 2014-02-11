# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011-2012 Domsense s.r.l. (<http://www.domsense.com>).
#    Copyright (C) 2012-2013 Agile Business Group sagl
#    (<http://www.agilebg.com>)
#    Copyright (C) 2014 Develer srl (<http://www.develer.com>)
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


class res_partner(orm.Model):
    _inherit = 'res.partner'

    _columns = {
        # the following field is a selection to force the user to select a value (a required boolean field may easily lead to errors)
        'default_has_vat_on_payment': fields.selection([('empty', ''), ('true', 'Has VAT on Payment'), ('false', 'No VAT on Payment')], 'VAT on Payment Default Flag', required=True),
    }

    _defaults = {
        'default_has_vat_on_payment': lambda *x: 'empty',
    }

    def _check_default_has_vat_on_payment(self, cr, uid, ids, context=None):
        for partner_id in self.browse(cr, uid, ids, context=context):
            if partner_id.default_has_vat_on_payment == 'empty':
                return False
        return True

    _constraints = [
        (_check_default_has_vat_on_payment, 'Default value for VAT on Payment flag must be set.', ['default_has_vat_on_payment']),
    ]
