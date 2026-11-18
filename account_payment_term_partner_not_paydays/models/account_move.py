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
        partner_payment_days = self.partner_id.with_context(
            move_type=self.move_type
        )._get_payment_days()
        if not partner_payment_days:
            return []
        return self.env["account.payment.term.line"]._decode_payment_days(
            partner_payment_days
        )

    @api.depends(
        "invoice_payment_term_id",
        "invoice_date_due",
        "partner_id",
        "invoice_date",
        "partner_id.partner_not_pay_ids.date_start",
        "partner_id.partner_not_pay_ids.date_end",
        "partner_id.partner_not_pay_ids.type",
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
                        "(%(range_overlap)s) of not pay to the partner. "
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

    def _in_not_pay_range(self, compare_date):
        return bool(
            self.partner_id._check_partner_range_not_pay(
                compare_date=compare_date, move_type=self.move_type
            )
        )

    def generate_invoice_date_due(self, due_date=None):
        """Return the payment day that replaces a due date falling in one of
        the partner's non-payment ranges. Without a date, the due date of the
        invoice is used.

        Month by month, starting with the month of the due date, only the
        payment days on or after the day of the due date are tried, and the
        first one later than the due date and outside every range wins. When
        the partner has none of them, all its payment days are tried, and
        without payment days the day of the due date is kept.
        """
        due_date = due_date or self.invoice_date_due
        pay_days = self.get_pay_days() or [due_date.day]
        candidate_days = [day for day in pay_days if day >= due_date.day] or pay_days
        month = due_date + relativedelta(day=1)
        while True:
            for pay_day in candidate_days:
                candidate = self.next_with_day(month, pay_day)
                if candidate > due_date and not self._in_not_pay_range(candidate):
                    return candidate
            month += relativedelta(months=1)

    def _post(self, soft=True):
        # The confirm button, the list action and the auto-post cron all post
        # through here.
        posted = super()._post(soft=soft)
        for move in posted.filtered(lambda move: move._check_day_not_pay()):
            term_lines = move.line_ids.filtered(
                lambda line: line.display_type == "payment_term"
            )
            lines_in_range = term_lines.filtered(
                lambda line, move=move: move._in_not_pay_range(line.date_maturity)
            )
            for line in lines_in_range:
                line.date_maturity = move.generate_invoice_date_due(line.date_maturity)
            if lines_in_range:
                move.invoice_date_due = max(term_lines.mapped("date_maturity"))
        return posted
