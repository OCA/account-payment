# -*- coding: utf-8 -*-

from openerp import fields, models


class AccountJournal(models.Model):

    _inherit = "account.journal"

    support_creditcard_transactions = fields.Boolean(
        string='Transfer AP to Credit Card Company',
    )

    partner_id = fields.Many2one(
        string='Credit Card Company',
        comodel_name='res.partner',
    )
