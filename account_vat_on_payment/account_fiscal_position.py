# -*- coding: utf-8 -*-
# © 2011-2012 Domsense s.r.l. (<http://www.domsense.com>).
# © 2014 Agile Business Group sagl (<http://www.agilebg.com>)
# © 2014 Develer srl (<http://www.develer.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.osv import fields, orm


class AccountFiscalPosition(orm.Model):
    _inherit = 'account.fiscal.position'

    _columns = {
        'default_has_vat_on_payment': fields.boolean(
            'VAT on Payment Default Flag'),
    }
