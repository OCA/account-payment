# -*- coding: utf-8 -*-
# Copyright 2019 Eficent Business and IT Consulting Services, S.L.

from odoo import api, models, fields, _
from odoo.exceptions import UserError


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.model
    def update_amount_reconcile(
            self, amount_reconcile, amount_reconcile_currency,
            sm_credit_move, sm_debit_move):
        super(AccountMoveLine, self).update_amount_reconcile(
            amount_reconcile, amount_reconcile_currency,
            sm_credit_move, sm_debit_move)
        # Check for the currency and amount_currency we can set
        amount_reconcile_currency = 0

        # Check if amount in context and if amount is positive
        paid_amt = self.env.context.get('paid_amount', False)
        if not paid_amt:
            return amount_reconcile, amount_reconcile_currency
        paid_amt = float(paid_amt)
        if paid_amt < 0:
            raise UserError(_(
                "The specified amount has to be strictly positive"))

        if sm_debit_move.currency_id == sm_credit_move.currency_id \
                and sm_debit_move.currency_id.id:
            amount_reconcile_currency = min(
                sm_debit_move.amount_residual_currency,
                -sm_credit_move.amount_residual_currency, paid_amt)
            paid_amt = sm_debit_move.currency_id.with_context(
                date=sm_credit_move.date or fields.Date.today()).compute(
                paid_amt, sm_debit_move.company_id.currency_id)
        amount_reconcile = min(sm_debit_move.amount_residual,
                               -sm_credit_move.amount_residual, paid_amt)

        return amount_reconcile, amount_reconcile_currency
