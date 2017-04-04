# -*- coding: utf-8 -*-
# Copyright 2015 OBERTIX FREE SOLUTIONS (<http://obertix.net>)
# Copyright 2015 cubells <vicent@vcubells.net>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    payment_mode_id = fields.Many2one(
        comodel_name='account.payment.mode',
        related='invoice_id.payment_mode_id',
        string="Payment Mode",
        store=True,
    )
