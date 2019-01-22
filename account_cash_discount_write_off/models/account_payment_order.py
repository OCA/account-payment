# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountPaymentOrder(models.Model):

    _inherit = 'account.payment.order'

    @api.multi
    def generated2uploaded(self):
        res = super(AccountPaymentOrder, self).generated2uploaded()
        for order in self:
            order._create_cash_discount_write_off()
        return res

    @api.multi
    def _create_cash_discount_write_off(self):
        self.ensure_one()
        for payment_line in self.payment_line_ids:
            if payment_line._check_cash_discount_write_off_creation():
                self._create_payment_line_discount_write_off(payment_line)

    @api.multi
    def _create_payment_line_discount_write_off(self, payment_line):
        self.ensure_one()
        move = self._create_payment_line_discount_write_off_move(payment_line)
        move_lines = payment_line.move_line_id | move.line_ids
        lines_to_reconcile = move_lines.filtered(
            lambda line:
            not line.reconciled and
            line.account_id == payment_line.move_line_id.account_id
        )
        lines_to_reconcile.reconcile()

    @api.multi
    def _create_payment_line_discount_write_off_move(self, payment_line):
        self.ensure_one()
        move_values = payment_line.get_cash_discount_writeoff_move_values()
        move = self.env['account.move'].create(move_values)
        if self.payment_mode_id.post_move:
            move.post()
        return move
