# Copyright 2018 Eficent Business and IT Consulting Services S.L.

from odoo.addons.account.models.account_move import AccountMoveLine


def post_load_hook():
    def _reconcile_lines_new(self, debit_moves, credit_moves, field):
        """ This function loops on the 2 recordsets given as parameter as
            long as it can find a debit and a credit to reconcile together.
            It returns the recordset of the account move lines that were not
            reconciled during the process.
        """
        if not hasattr(self, 'update_amount_reconcile'):
            return self._reconcile_lines_original()

        (debit_moves + credit_moves).read([field])
        to_create = []
        cash_basis = debit_moves and debit_moves[
            0].account_id.internal_type in ('receivable', 'payable') or False
        cash_basis_percentage_before_rec = {}
        dc_vals = {}
        while (debit_moves and credit_moves):
            debit_move = debit_moves[0]
            credit_move = credit_moves[0]
            # company_currency = debit_move.company_id.currency_id
            # We need those temporary value otherwise the computation might
            # be wrong below
            temp_amount_residual = min(debit_move.amount_residual,
                                       -credit_move.amount_residual)
            temp_amount_residual_currency = min(
                debit_move.amount_residual_currency,
                -credit_move.amount_residual_currency)

            dc_vals[(debit_move.id, credit_move.id)] = (
                debit_move, credit_move, temp_amount_residual_currency)
            amount_reconcile = min(debit_move[field], -credit_move[field])

            # Start Hook
            temp_amount_residual, temp_amount_residual_currency, \
                amount_reconcile = self.update_amount_reconcile(
                    temp_amount_residual, temp_amount_residual_currency,
                    amount_reconcile, credit_move, debit_move)
            # End Hook

            # Remove from recordset the one(s) that will be totally reconciled
            # For optimization purpose, the creation of the partial_reconcile
            # are done at the end, therefore during the process of reconciling
            # several move lines, there are actually no recompute performed by
            # the orm and thus the amount_residual are not recomputed, hence
            # we have to do it manually.
            # Hook - add method _check_remove_debit_move
            if self._check_remove_debit_move(amount_reconcile,
                                             debit_move, field):
                debit_moves -= debit_move
            else:
                debit_moves[0].amount_residual -= temp_amount_residual
                debit_moves[0].amount_residual_currency -= \
                    temp_amount_residual_currency
            # Hook - add method _check_remove_credit_move
            if self._check_remove_credit_move(amount_reconcile,
                                              credit_move, field):
                credit_moves -= credit_move
            else:
                credit_moves[0].amount_residual += temp_amount_residual
                credit_moves[0].amount_residual_currency += \
                    temp_amount_residual_currency
            # Check for the currency and amount_currency we can set
            currency = False
            amount_reconcile_currency = 0
            if field == 'amount_residual_currency':
                currency = credit_move.currency_id.id
                amount_reconcile_currency = temp_amount_residual_currency
                amount_reconcile = temp_amount_residual

            if cash_basis:
                tmp_set = debit_move | credit_move
                cash_basis_percentage_before_rec.update(
                    tmp_set._get_matched_percentage())

            to_create.append({
                'debit_move_id': debit_move.id,
                'credit_move_id': credit_move.id,
                'amount': amount_reconcile,
                'amount_currency': amount_reconcile_currency,
                'currency_id': currency,
            })

        cash_basis_subjected = []
        part_rec = self.env['account.partial.reconcile']
        with self.env.norecompute():
            for partial_rec_dict in to_create:
                debit_move, credit_move, amount_residual_currency = dc_vals[
                    partial_rec_dict['debit_move_id'], partial_rec_dict[
                        'credit_move_id']]
                # /!\ NOTE: Exchange rate differences shouldn't create cash
                # basis entries i. e: we don't really receive/give money in a
                # customer/provider fashion
                # Since those are not subjected to cash basis computation we
                # process them first
                if not amount_residual_currency and debit_move.currency_id and\
                        credit_move.currency_id:
                    part_rec.create(partial_rec_dict)
                else:
                    cash_basis_subjected.append(partial_rec_dict)

            for after_rec_dict in cash_basis_subjected:
                new_rec = part_rec.create(after_rec_dict)
                # if the pair belongs to move being reverted, do not create
                # CABA entry
                if cash_basis and not (
                        new_rec.debit_move_id + new_rec.credit_move_id).mapped(
                        'move_id').mapped('reverse_entry_id'):
                    new_rec.create_tax_cash_basis_entry(
                        cash_basis_percentage_before_rec)
        self.recompute()

        return debit_moves + credit_moves

    if not hasattr(AccountMoveLine, 'auto_reconcile_lines_original'):
        AccountMoveLine._reconcile_lines_original = AccountMoveLine.\
            _reconcile_lines
    AccountMoveLine._reconcile_lines = _reconcile_lines_new
