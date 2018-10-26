# -*- coding: utf-8 -*-
# Copyright 2017 Ursa Information Systems <http://www.ursainfosystems.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from openerp import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    credit_card = fields.Boolean(string='Credit Card Payment',
                                 help='Transfer AP to Credit Card Company')
    partner_id = fields.Many2one('res.partner', string='Credit Card Company',
                                 domain=[('supplier', '=', True)],
                                 help='Choose the credit card issuer')
