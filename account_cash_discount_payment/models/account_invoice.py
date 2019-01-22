# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.tools import float_compare


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    @api.multi
    def _can_pay_invoice_with_discount(self, check_due_date=True):
        self.ensure_one()
        today = fields.Date.today()
        rounding = self.currency_id.rounding
        if not self.has_discount:
            return False

        refunds_amount_total = 0.0
        for pmove_line in self.payment_move_line_ids:
            pmove_line_inv = pmove_line.invoice_id
            if pmove_line_inv and pmove_line_inv.type == 'in_refund':
                refunds_amount_total += pmove_line_inv.amount_total

        if check_due_date:
            date_check_valid = self.discount_due_date >= today
        else:
            date_check_valid = True

        return (
            date_check_valid and
            float_compare(
                self.residual,
                self.amount_total - refunds_amount_total,
                precision_rounding=rounding,
            ) == 0
        )
