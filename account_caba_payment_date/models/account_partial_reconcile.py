# Copyright 2024 Jarsa (https://www.jarsa.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from datetime import date as date_lib
from datetime import timedelta

from odoo import _, models
from odoo.exceptions import UserError


class AccountPartialReconcile(models.Model):
    _inherit = "account.partial.reconcile"

    def _caba_get_payment_date(self):
        """Return the real payment date of the reconciliation: the date of the
        bank/cash journal entry when there is one, the newest date otherwise."""
        self.ensure_one()
        for line in (self.debit_move_id, self.credit_move_id):
            if line.journal_id.type in ("bank", "cash"):
                return line.date
        return self.max_date

    def _create_tax_cash_basis_moves(self):
        moves = super()._create_tax_cash_basis_moves()
        for move in moves:
            partial = move.tax_cash_basis_rec_id
            if not partial:
                continue
            date = partial._caba_get_payment_date()
            # The tax lock date also applies: the cash basis entry affects the
            # tax report, so it cannot be dated inside a tax-locked period.
            lock_date = max(
                move.company_id._get_user_fiscal_lock_date(),
                move.company_id.max_tax_lock_date or date_lib.min,
            )
            if date <= lock_date:
                policy = move.company_id.caba_payment_date_lock_policy
                if policy == "standard":
                    continue
                if policy == "next_open":
                    date = lock_date + timedelta(days=1)
                else:  # block
                    raise UserError(
                        _(
                            "The cash basis entry of this reconciliation must be "
                            "dated on the payment date %(date)s, but that period "
                            "is locked "
                            "(lock date: %(lock_date)s).\n"
                            "Reopen the period, or change the cash basis lock policy "
                            "in the accounting settings.",
                            date=date,
                            lock_date=lock_date,
                        )
                    )
            if date != move.date:
                month_changed = (date.year, date.month) != (
                    move.date.year,
                    move.date.month,
                )
                vals = {"date": date}
                if month_changed:
                    # Clear the name so the date-sequence constraint does not
                    # reject the write, then resequence for the new period.
                    vals["name"] = False
                move.write(vals)
                if month_changed:
                    move._compute_name()
        return moves
