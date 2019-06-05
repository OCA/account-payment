# -*- coding: utf-8 -*-
# Copyright 2019 Eficent Business and IT Consulting Services, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    amount_residual = fields.Monetary(
        compute='_amount_residual',
        string='Residual Amount', store=True,
        currency_field='currency_id',
        help="The residual amount on a journal item "
             "expressed in the company currency.")

    @api.multi
    @api.depends('move_line_ids',
                 'move_line_ids.amount_residual',
                 'move_line_ids.amount_residual_currency')
    def _amount_residual(self):
        for payment in self:
            amount_residual = 0.0
            amount_residual_currency = 0.0
            pay_acc = payment.journal_id.default_debit_account_id or \
                payment.journal_id.default_credit_account_id
            for aml in payment.move_line_ids.filtered(
                    lambda x: x.account_id.reconcile
                    and x.account_id != pay_acc):
                amount_residual += aml.amount_residual
                amount_residual_currency += aml.amount_residual_currency
            if payment.payment_type == 'inbound':
                amount_residual *= -1
                amount_residual_currency *= -1
            if payment.currency_id != payment.company_id.currency_id:
                payment.amount_residual = amount_residual_currency
            else:
                payment.amount_residual = amount_residual
