# -*- coding: utf-8 -*-
# © 2011-2012 Domsense s.r.l. (<http://www.domsense.com>).
# © 2014 Agile Business Group sagl (<http://www.agilebg.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.osv import orm, fields


class AccountMoveLine(orm.Model):
    _inherit = "account.move.line"
    _columns = {
        'real_payment_move_id': fields.many2one(
            'account.move', 'Real payment entry'),
        'real_account_id': fields.many2one('account.account', 'Real account'),
        'real_tax_code_id': fields.many2one(
            'account.tax.code', 'Real tax code'),
    }
