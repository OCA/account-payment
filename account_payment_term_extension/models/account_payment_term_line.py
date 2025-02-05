# Copyright 2013-2016 Camptocamp SA (Yannick Vaucher)
# Copyright 2004-2016 Odoo S.A. (www.odoo.com)
# Copyright 2015-2016 Akretion
# (Alexis de Lattre <alexis.delattre@akretion.com>)
# Copyright 2018 Simone Rubino - Agile Business Group
# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from dateutil.relativedelta import relativedelta

from odoo import api, exceptions, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import date_utils
from odoo.tools.float_utils import float_round


class AccountPaymentTermLine(models.Model):
    _inherit = "account.payment.term.line"

    amount_round = fields.Float(
        string="Amount Rounding",
        digits="Account",
        help="Sets the amount so that it is a multiple of this value.",
    )
    delay_type = fields.Selection(
        selection=lambda self: self._get_delay_type(),
        ondelete={
            "weeks_after": "set default",
            "weeks_after_end_of_month": "set default",
            "weeks_after_end_of_next_month": "set default",
            "months_after": "set default",
            "months_after_end_of_month": "set default",
        },
    )
    value = fields.Selection(
        selection_add=[
            ("percent_amount_untaxed", "Percent (Untaxed amount)"),
            ("fixed",),
        ],
        ondelete={"percent_amount_untaxed": lambda r: r.write({"value": "percent"})},
    )

    payment_days = fields.Char(
        string="Payment day(s)",
        help="Put here the day or days when the partner makes the payment. "
        "Separate each possible payment day with dashes (-), commas (,) "
        "or spaces ( ).",
    )

    def _get_delay_type(self):
        delay_setting = self.env.company.payment_terms_delay_type
        payment_terms_delay_type = delay_setting or False

        delay_type = [
            ("days_after", "Days after invoice date"),
            ("days_after_end_of_month", "Days after end of month"),
            ("days_after_end_of_next_month", "Days after end of next month"),
            ("days_end_of_month_on_the", "Days end of month on the"),
        ]

        weeks_delay_type = [
            ("weeks_after", "Weeks after invoice date"),
            ("weeks_after_end_of_month", "Weeks after end of month"),
            ("weeks_after_end_of_next_month", "Weeks after end of next month"),
        ]
        months_delay_type = [
            ("months_after", "Months after invoice date"),
            ("months_after_end_of_month", "Months after end of month"),
        ]

        if payment_terms_delay_type:
            if payment_terms_delay_type:
                if payment_terms_delay_type == "months":
                    delay_type += months_delay_type
                elif payment_terms_delay_type == "weeks":
                    delay_type += weeks_delay_type
                elif payment_terms_delay_type == "weeks_and_months":
                    delay_type += weeks_delay_type + months_delay_type
        return delay_type

    def _decode_payment_days(self, days_char):
        # Admit space, dash and comma as separators
        days_char = days_char.replace(" ", "-").replace(",", "-")
        days_char = [x.strip() for x in days_char.split("-") if x]
        days = [int(x) for x in days_char]
        days.sort()
        return days

    @api.constrains("payment_days")
    def _check_payment_days(self):
        for record in self:
            if not record.payment_days:
                continue
            try:
                payment_days = record._decode_payment_days(record.payment_days)
                error = any(day <= 0 or day > 31 for day in payment_days)
            except Exception:
                error = True
            if error:
                raise exceptions.UserError(
                    self.env._("Payment days field format is not valid.")
                )

    def _get_due_date(self, date_ref):
        res = super()._get_due_date(date_ref)
        due_date = fields.Date.from_string(date_ref) or fields.Date.today()
        if self.delay_type == "weeks_after":
            return due_date + relativedelta(weeks=self.nb_days)
        elif self.delay_type == "weeks_after_end_of_month":
            return date_utils.end_of(due_date, "month") + relativedelta(
                weeks=self.nb_days
            )
        elif self.delay_type == "weeks_after_end_of_next_month":
            return date_utils.end_of(
                due_date + relativedelta(months=1), "month"
            ) + relativedelta(weeks=self.nb_days)
        elif self.delay_type == "months_after":
            return due_date + relativedelta(months=self.nb_days)
        elif self.delay_type == "months_after_end_of_month":
            return date_utils.end_of(due_date, "month") + relativedelta(
                months=self.nb_days
            )
        return res

    @api.constrains("value", "value_amount")
    def _check_value_amount_untaxed(self):
        for term_line in self:
            if (
                term_line.value == "percent_amount_untaxed"
                and not 0 <= term_line.value_amount <= 100
            ):
                raise ValidationError(
                    self.env._(
                        "Percentages on the Payment Terms lines "
                        "must be between 0 and 100."
                    )
                )

    def compute_line_amount(self, total_amount, remaining_amount, precision_digits):
        """Compute the amount for a payment term line.
        In case of procent computation, use the payment
        term line rounding if defined

            :param total_amount: total balance to pay
            :param remaining_amount: total amount minus sum of previous lines
                computed amount
            :returns: computed amount for this line
        """
        self.ensure_one()
        if self.value == "fixed":
            return float_round(self.value_amount, precision_digits=precision_digits)
        elif self.value in ("percent", "percent_amount_untaxed"):
            amt = total_amount * self.value_amount / 100.0
            if self.amount_round:
                amt = float_round(amt, precision_rounding=self.amount_round)
            return float_round(amt, precision_digits=precision_digits)
        elif self.value == "balance":
            return float_round(remaining_amount, precision_digits=precision_digits)
        return None
