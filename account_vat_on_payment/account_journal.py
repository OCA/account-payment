# -*- coding: utf-8 -*-
# © 2011-2012 Domsense s.r.l. (<http://www.domsense.com>).
# © 2014 Agile Business Group sagl (<http://www.agilebg.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.osv import orm, fields


class AccountJournal(orm.Model):
    _inherit = "account.journal"
    _columns = {
        'vat_on_payment_related_journal_id': fields.many2one(
            'account.journal', 'Shadow Journal for VAT on payment',
            help="Related journal used for shadow registrations on a "
                 "VAT on payment basis. Set the shadow journal here"),
    }
