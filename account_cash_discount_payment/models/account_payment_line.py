# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields


class PaymentLine(models.Model):

    _inherit = 'account.payment.line'

    pay_with_discount = fields.Boolean(
        default=False,
    )
    discount_due_date = fields.Date(
        compute='_compute_discount_due_date',
    )
    discount_amount = fields.Monetary(
        default=0.0
    )
    original_amount_currency = fields.Monetary(
        readonly=True,
    )

    @api.multi
    @api.depends(
        'move_line_id.invoice_id'
    )
    def _compute_discount_due_date(self):
        for rec in self:
            if rec.move_line_id and rec.move_line_id.invoice_id:
                invoice = rec.move_line_id.invoice_id
                rec.discount_due_date = invoice.discount_due_date

    @api.onchange(
        'discount_amount',
        'original_amount_currency',
        'pay_with_discount',
    )
    def _onchange_pay_with_discount(self):
        if self.pay_with_discount:
            self.amount_currency = (
                self.original_amount_currency - self.discount_amount)
        else:
            self.amount_currency = self.original_amount_currency
