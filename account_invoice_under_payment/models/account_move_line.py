# -*- coding: utf-8 -*-
# Copyright 2016 Serpent Consulting Services Pvt. Ltd
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from openerp import models, fields, api


class AccountMoveline(models.Model):
    _inherit = "account.move.line"

    @api.multi
    @api.depends('payment_line_ids.failed', 'payment_line_ids.move_line_id')
    def _check_payment(self):
        for line in self:
            line.under_payment = any(
                [not x.failed for x in line.payment_line_ids])

    payment_line_ids = fields.One2many(
        'payment.line', 'move_line_id', string='Payment Lines', readonly=True)

    under_payment = fields.Boolean(
        'Under Payment', readonly=True, store=True, compute=_check_payment)
