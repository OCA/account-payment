# -*- coding: utf-8 -*-
# © 2015 Eficent
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp.osv import orm, fields


class ResPartner(orm.Model):
    _inherit = "res.partner"

    _columns = {
        'type': fields.selection(
            [('default', 'Default'), ('invoice', 'Invoice'),
             ('delivery', 'Shipping'), ('contact', 'Contact'),
             ('other', 'Other'), ('remit_to', 'Remit-to')],
            'Address Type',
            help="Used to select automatically the right address "
                 "according to the context in sales and "
                 "purchases documents."),

    }
