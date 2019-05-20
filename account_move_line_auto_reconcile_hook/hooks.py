# -*- coding: utf-8 -*-
# Copyright 2018 Eficent Business and IT Consulting Services S.L.

from odoo.addons.account.models.account_move import AccountMoveLine


def post_load_hook():
    def new_auto_reconcile_lines(self):
        """ This function iterates recursively on the recordset given as
            parameter as long as it can find a debit and a credit to reconcile
            together. It returns the recordset of the account move lines that
            were not reconciled during the process.
        """
        if not hasattr(self, 'update_amount_reconcile'):
            return self.auto_reconcile_lines_original()

        if not self.ids:
            return self
        sm_debit_move, sm_credit_move = self._get_pair_to_reconcile()
        # there is no more pair to reconcile so return what move_line are left
        if not sm_credit_move or not sm_debit_move:
            return self

        field = self[0].account_id.currency_id \
            and 'amount_residual_currency' or 'amount_residual'
        if not sm_debit_move.debit and not sm_debit_move.credit:
            # both debit and credit field are 0, consider the amount_residual_
            # currency field because it's an exchange difference entry
            field = 'amount_residual_currency'
        if self[0].currency_id and all(
                [x.currency_id == self[0].currency_id for x in self]):
            # all the lines have the same currency, so we consider the amount_
            # residual_currency field
            field = 'amount_residual_currency'
        if self._context.get(
                'skip_full_reconcile_check') == 'amount_currency_excluded':
            field = 'amount_residual'
        elif self._context.get(
                'skip_full_reconcile_check') == 'amount_currency_only':
            field = 'amount_residual_currency'
        # Reconcile the pair together
        amount_reconcile = min(sm_debit_move[field], -sm_credit_move[field])
        # Remove from recordset the one(s) that will be totally reconciled
        if amount_reconcile == sm_debit_move[field]:
            self -= sm_debit_move
        if amount_reconcile == -sm_credit_move[field]:
            self -= sm_credit_move

        # Check for the currency and amount_currency we can set
        currency = False
        amount_reconcile_currency = 0
        if sm_debit_move.currency_id == sm_credit_move.currency_id and \
                sm_debit_move.currency_id.id:
            currency = sm_credit_move.currency_id.id
            amount_reconcile_currency = min(
                sm_debit_move.amount_residual_currency,
                -sm_credit_move.amount_residual_currency)

        amount_reconcile = min(sm_debit_move.amount_residual,
                               -sm_credit_move.amount_residual)

        # Start hook
        amount_reconcile, amount_reconcile_currency = \
            self.update_amount_reconcile(
                amount_reconcile, amount_reconcile_currency,
                sm_credit_move, sm_debit_move)
        # End Hook

        if self._context.get(
                'skip_full_reconcile_check') == 'amount_currency_excluded':
            amount_reconcile_currency = 0.0
            currency = self._context.get('manual_full_reconcile_currency')
        elif self._context.get(
                'skip_full_reconcile_check') == 'amount_currency_only':
            currency = self._context.get('manual_full_reconcile_currency')

        self.env['account.partial.reconcile'].create({
            'debit_move_id': sm_debit_move.id,
            'credit_move_id': sm_credit_move.id,
            'amount': amount_reconcile,
            'amount_currency': amount_reconcile_currency,
            'currency_id': currency,
        })

        # Iterate process again on self
        return self.auto_reconcile_lines()

    if not hasattr(AccountMoveLine, 'auto_reconcile_lines_original'):
        AccountMoveLine.auto_reconcile_lines_original = AccountMoveLine.\
            auto_reconcile_lines
    AccountMoveLine.auto_reconcile_lines = new_auto_reconcile_lines
