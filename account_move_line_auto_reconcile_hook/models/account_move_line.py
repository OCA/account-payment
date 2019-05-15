# -*- coding: utf-8 -*-

from odoo import api, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.model
    def update_amount_reconcile(
            self, amount_reconcile, amount_reconcile_currency,
            sm_credit_move, sm_debit_move):
        return amount_reconcile, amount_reconcile_currency
