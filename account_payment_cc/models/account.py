# -*- coding: utf-8 -*-


from openerp.osv import fields, osv


class AccountJournal(osv.osv):

    _inherit = "account.journal"

    _columns = {
        'support_creditcard_transactions': fields.boolean('Transfer AP to '
                                                          'Credit Card '
                                                          'Company',),
        'partner_id': fields.many2one('res.partner', 'Credit Card Company'),
    }
