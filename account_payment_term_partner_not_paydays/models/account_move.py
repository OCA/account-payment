# Copyright 2025 Binhex <https://www.binhex.cloud>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    message_range_not_pay = fields.Char(compute="_compute_message_range_not_pay")
    invoice_date_due = fields.Date(tracking=True)

    def _check_day_not_pay(self):
        return (
            self.partner_id
            and self.partner_id.days_not_pay
            and self.partner_id.partner_not_pay_ids
        )

    def next_with_day(self, base_date, day_pay):
        target_pay = day_pay
        if day_pay <= 0:
            target_pay = base_date.day
        return base_date + relativedelta(day=target_pay)

    def get_pay_days(self):
        PaymentTermLine = self.env["account.payment.term.line"]
        partner_payment_days = self.partner_id.with_context(
            move_type=self.move_type
        )._get_payment_days()
        if partner_payment_days and self.invoice_date:
            current_day = self.invoice_date.day
            if current_day:
                payment_days = PaymentTermLine._decode_payment_days(
                    partner_payment_days
                )
                next_day = list(filter(lambda x: x >= current_day, payment_days))
                return next_day
        return False

    @api.depends(
        "invoice_payment_term_id", "invoice_date_due", "partner_id", "invoice_date"
    )
    def _compute_message_range_not_pay(self):
        for move in self:
            if move._check_day_not_pay():
                overlap = move.partner_id._check_partner_range_not_pay(
                    **{
                        "compare_date": move.invoice_date_due,
                        "move_type": move.move_type,
                    }
                )
                if overlap:
                    move.message_range_not_pay = _(
                        "The due date %(invoice_date_due)s falls within the period "
                        "(%(range_overlap)s) of not pay to the partner."
                        "If, upon confirming the invoice, the date mentioned does not "
                        "meet the conditions, said date will be changed to the "
                        "first valid one."
                    ) % {
                        "invoice_date_due": move.invoice_date_due.strftime("%d/%m/%Y"),
                        "range_overlap": overlap[0]["date_start"].strftime("%d/%m/%Y")
                        + " - "
                        + overlap[0]["date_end"].strftime("%d/%m/%Y"),
                    }
                else:
                    move.message_range_not_pay = False
            else:
                move.message_range_not_pay = False

    def _valid_overlap_date(self, compare_date, pay_day):
        overlap = self.partner_id._check_partner_range_not_pay(
            **{"compare_date": compare_date, "move_type": self.move_type}
        )
        if overlap:
            if not self.env.context.get("not_next_date", False):
                compare_date = self.next_with_day(
                    compare_date + relativedelta(months=1), pay_day
                )
            return compare_date
        return True

    def _reset_compare_date(self, pay_day):
        return self.next_with_day(
            self.invoice_date_due + relativedelta(months=1), pay_day
        )

    def generate_invoice_date_due(self):
        """
        Find the days on or above the current date and check for availability.

        If no available date is found, retrieve the first payday and
        check subsequent months for available paydays.
        """
        pay_days = self.get_pay_days() or [self.invoice_date_due.day]
        for pay_day in pay_days:
            compare_date = self._reset_compare_date(pay_day)
            overlap_date = self.with_context(
                **{"not_next_date": True}
            )._valid_overlap_date(compare_date, pay_day)
            if overlap_date is True:
                return compare_date

        pay_day = pay_days[0] if pay_days else self.invoice_date_due.day
        compare_date = self._reset_compare_date(pay_day)
        while True:
            overlap_date = self._valid_overlap_date(compare_date, pay_day)
            if overlap_date is True:
                return compare_date
            compare_date = overlap_date

    def action_post(self):
        moves = super().action_post()
        for move in self:
            if move.message_range_not_pay and move._check_day_not_pay():
                move.invoice_date_due = move.generate_invoice_date_due()
        return moves
