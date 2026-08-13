# Copyright 2026 PopSolutions
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from collections import defaultdict

from odoo import models

# Percentages are stored as floats, rounding keeps the plain cases exact
# (a single analytic account spread over several journal items must give 100.0)
DISTRIBUTION_PRECISION = 6

COUNTERPART_ACCOUNT_TYPES = ("asset_receivable", "liability_payable")


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    def _get_analytic_distribution_source_lines(self, lines):
        """Return the journal items holding the analytic information to copy.

        The receivable/payable lines are left out: they carry no analytic
        distribution of their own and their balance would weight the result
        down by half.

        :param lines: the journal items being paid.
        :return: an ``account.move.line`` recordset.
        """
        return lines.move_id.line_ids.filtered(
            lambda line: line.account_id.account_type not in COUNTERPART_ACCOUNT_TYPES
        )

    def _get_analytic_distribution_from_lines(self, lines):
        """Aggregate the analytic distribution of the documents being paid.

        Each journal item weights on the result in proportion to its own
        balance, so an invoice split 90/10 between two analytic accounts is
        paid 90/10 and not 50/50. Amounts carrying no analytic account on the
        invoice stay unallocated on the payment as well.

        :param lines: the journal items being paid.
        :return: an ``analytic_distribution`` dict, or ``False`` when the paid
            documents hold no analytic distribution at all.
        """
        weight_per_account = defaultdict(float)
        total_weight = 0.0
        for line in self._get_analytic_distribution_source_lines(lines):
            weight = abs(line.balance)
            if not weight:
                continue
            total_weight += weight
            for account_ids, percentage in (line.analytic_distribution or {}).items():
                weight_per_account[account_ids] += weight * percentage
        if not (total_weight and weight_per_account):
            return False
        return {
            account_ids: round(weight / total_weight, DISTRIBUTION_PRECISION)
            for account_ids, weight in weight_per_account.items()
        }

    def _init_payments(self, to_process, edit_mode=False):
        """Copy the analytic distribution of the paid documents to the payments.

        The distribution is written while the payments are still in draft, so
        that the analytic items are created once, when the payment is posted.
        """
        payments = super()._init_payments(to_process, edit_mode=edit_mode)
        for values in to_process:
            distribution = self._get_analytic_distribution_from_lines(
                values["to_reconcile"]
            )
            if not distribution:
                continue
            counterpart_lines = values["payment"]._seek_for_lines()[1]
            counterpart_lines.filtered(
                lambda line: not line.analytic_distribution
            ).analytic_distribution = distribution
        return payments
