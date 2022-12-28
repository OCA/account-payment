# Copyright 2022 ForgeFlow, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import _
from odoo.exceptions import UserError

from odoo.addons.account.models.account_payment import (
    AccountPayment as AccountPaymentClass,
)


def post_load_hook():  # noqa: C901
    def _synchronize_from_moves_new(self, changed_fields):
        if not self.line_payment_counterpart_ids:
            return self._synchronize_from_moves_original(changed_fields)
        if self._context.get("skip_account_move_synchronization"):
            return

        for pay in self.with_context(skip_account_move_synchronization=True):

            if pay.move_id.statement_line_id:
                continue

            move = pay.move_id
            move_vals_to_write = {}
            payment_vals_to_write = {}

            if "journal_id" in changed_fields:
                if pay.journal_id.type not in ("bank", "cash"):
                    raise UserError(
                        _("A payment must always belongs to a bank or cash journal.")
                    )

            if "line_ids" in changed_fields:
                all_lines = move.line_ids
                (
                    liquidity_lines,
                    counterpart_lines,
                    writeoff_lines,
                ) = pay._seek_for_lines()

                if any(
                    line.currency_id != all_lines[0].currency_id for line in all_lines
                ):
                    raise UserError(
                        _(
                            "Journal Entry %s is not valid. "
                            "In order to proceed, "
                            "the journal items must "
                            "share the same currency.",
                            move.display_name,
                        )
                    )

                if "receivable" in counterpart_lines.mapped(
                    "account_id.user_type_id.type"
                ):
                    partner_type = "customer"
                else:
                    partner_type = "supplier"

                liquidity_amount = liquidity_lines.amount_currency

                move_vals_to_write.update(
                    {
                        "currency_id": liquidity_lines.currency_id.id,
                        "partner_id": liquidity_lines.partner_id.id,
                    }
                )
                destination_account_id = counterpart_lines.mapped("account_id")[0].id
                payment_vals_to_write.update(
                    {
                        "amount": abs(liquidity_amount),
                        "partner_type": partner_type,
                        "currency_id": liquidity_lines.currency_id.id,
                        "destination_account_id": destination_account_id,
                        "partner_id": liquidity_lines.partner_id.id,
                    }
                )
                if liquidity_amount > 0.0:
                    payment_vals_to_write.update({"payment_type": "inbound"})
                elif liquidity_amount < 0.0:
                    payment_vals_to_write.update({"payment_type": "outbound"})

            move.write(move._cleanup_write_orm_values(move, move_vals_to_write))
            pay.write(move._cleanup_write_orm_values(pay, payment_vals_to_write))

    if not hasattr(AccountPaymentClass, "_synchronize_from_moves_original"):
        AccountPaymentClass._synchronize_from_moves_original = (
            AccountPaymentClass._synchronize_from_moves
        )
    AccountPaymentClass._synchronize_from_moves = _synchronize_from_moves_new
