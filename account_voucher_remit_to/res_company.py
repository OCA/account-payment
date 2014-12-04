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

from openerp.osv import osv,fields

class res_company(osv.osv):
    _inherit = "res.company"

    _columns = {
        'property_partner_rel_remit': fields.property(
            'res.partner.relation.type',
            type='many2one',
            relation='res.partner.relation.type',
            string="Remit-to relation type",
            view_load=True,
            help="This type of relationship will be used, "
                 "during the preparation of account vouchers "
                 "to determine the remit-to address."),
    }

res_company()

