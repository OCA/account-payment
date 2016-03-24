# -*- coding: utf-8 -*-
# (c) 2015 brain-tec AG (http://www.braintec-group.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# import time
from openerp import models, fields


class PaymentMode(models.Model):
    _name = 'payment.mode'
    _description = 'Payment Mode'

    name = fields.Char('Name', required=True, help='Mode of Payment')

    bank_id = fields.Many2one('res.partner.bank', "Bank account",
                              required=True,
                              help='Bank Account for the Payment Mode')

    journal_id = fields.Many2one('account.journal', 'Journal', required=True,
                                 domain=[('type', 'in', ('bank', 'cash'))],
                                 help='Bank or Cash Journal for the '
                                 'Payment Mode',oldname='journal')

    company_id = fields.\
        Many2one('res.company', 'Company', required=True,
                 default=lambda self: self.env.user.company_id.id)

    partner_id = fields.Many2one('res.partner',
                                 related='company_id.partner_id',
                                 string='Partner', store=True)
