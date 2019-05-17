# Copyright 2019 Eficent Business and IT Consulting Services, S.L.

from odoo import api, models, _
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

        # Check if amount is positive
        paid_amt = self.env.context.get('paid_amount', False)
        if paid_amt < 0:
            raise UserError(_(
                "The specified amount has to be strictly positive"))

        if sm_debit_move.currency_id == sm_credit_move.currency_id \
                and sm_debit_move.currency_id.id:
            paid_amt = paid_amt and min(
                float(paid_amt), -sm_credit_move.amount_residual_currency) or \
                -sm_credit_move.amount_residual_currency
            amount_reconcile_currency = min(
                sm_debit_move.amount_residual_currency, paid_amt)
            if paid_amt:
                paid_amt = paid_amt * sm_credit_move.company_currency_id.rate

        paid_amt = paid_amt and min(
            float(paid_amt), -sm_credit_move.amount_residual) or \
            -sm_credit_move.amount_residual
        amount_reconcile = min(sm_debit_move.amount_residual, paid_amt)

        return amount_reconcile, amount_reconcile_currency
