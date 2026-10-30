# Copyright 2013-2016 Camptocamp SA (Yannick Vaucher)
# Copyright 2004-2016 Odoo S.A. (www.odoo.com)
# Copyright 2015-2016 Akretion
# (Alexis de Lattre <alexis.delattre@akretion.com>)
# Copyright 2018 Simone Rubino - Agile Business Group
# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import calendar

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import UserError


class AccountPaymentTerm(models.Model):
    _inherit = "account.payment.term"

    sequential_lines = fields.Boolean(
        default=False,
        help="Allows to apply a chronological order on lines.",
    )
    holiday_ids = fields.One2many(
        string="Holidays",
        comodel_name="account.payment.term.holiday",
        inverse_name="payment_id",
    )

    def apply_holidays(self, date):
        holiday = self.holiday_ids.filtered(lambda holiday: holiday.holiday == date)[:1]
        if holiday:
            return holiday.date_postponed
        return date

    def apply_payment_days(self, line, date):
        """Calculate the new date with days of payments"""
        if line.payment_days:
            payment_days = line._decode_payment_days(line.payment_days)
            if payment_days:
                new_date = None
                payment_days.sort()
                days_in_month = calendar.monthrange(date.year, date.month)[1]
                for day in payment_days:
                    if date.day <= day:
                        day = min(day, days_in_month)
                        new_date = date + relativedelta(day=day)
                        break
                if not new_date:
                    day = payment_days[0]
                    day = min(day, days_in_month)
                    new_date = date + relativedelta(day=day, months=1)
                return new_date
        return date

    @api.depends(
        "currency_id",
        "example_amount",
        "example_date",
        "line_ids.value",
        "line_ids.value_amount",
        "line_ids.nb_days",
        "line_ids.delay_type",
        "line_ids.days_next_month",
        "line_ids.payment_days",
        "line_ids.amount_round",
        "early_discount",
        "discount_percentage",
        "discount_days",
        "sequential_lines",
        "holiday_ids",
        "holiday_ids.holiday",
        "holiday_ids.date_postponed",
    )
    def _compute_example_preview(self):
        """adding depends for new customized fields"""
        return super()._compute_example_preview()

    def _compute_terms(
        self,
        date_ref,
        currency,
        company,
        tax_amount,
        tax_amount_currency,
        sign,
        untaxed_amount,
        untaxed_amount_currency,
        cash_rounding=None,
    ):
        """Extend core amounts and rounding with custom dates and line amounts."""
        date_ref = fields.Date.to_date(date_ref)
        pay_term = super()._compute_terms(
            date_ref=date_ref,
            currency=currency,
            company=company,
            tax_amount=tax_amount,
            tax_amount_currency=tax_amount_currency,
            sign=sign,
            untaxed_amount=untaxed_amount,
            untaxed_amount_currency=untaxed_amount_currency,
            cash_rounding=cash_rounding,
        )
        company_currency = company.currency_id
        total_amount = tax_amount + untaxed_amount
        total_amount_currency = tax_amount_currency + untaxed_amount_currency
        residual_amount = total_amount
        residual_amount_currency = total_amount_currency
        rate = abs(total_amount_currency / total_amount) if total_amount else 0.0
        next_date = date_ref
        for i, (line, term_vals) in enumerate(
            zip(self.line_ids, pay_term["line_ids"], strict=True)
        ):
            next_date = (
                line._get_due_date(next_date)
                if self.sequential_lines
                else term_vals["date"]
            )
            next_date = self.apply_payment_days(line, next_date)
            next_date = self.apply_holidays(next_date)
            term_vals["date"] = next_date

            if i == len(self.line_ids) - 1:
                # Custom amounts on earlier lines change the final balance.
                term_vals["company_amount"] = residual_amount
                term_vals["foreign_amount"] = residual_amount_currency
            elif line.value == "percent_amount_untaxed" or (
                line.value == "percent" and line.amount_round
            ):
                if line.value == "percent_amount_untaxed":
                    if company_currency != currency:
                        raise UserError(
                            self.env._(
                                "Percentage of amount untaxed can't be used "
                                "with foreign currencies"
                            )
                        )
                    base_amount = untaxed_amount
                    base_amount_currency = untaxed_amount_currency
                else:
                    base_amount = total_amount
                    base_amount_currency = total_amount_currency
                term_vals["company_amount"] = line.compute_line_amount(
                    base_amount, residual_amount, company_currency.decimal_places
                )
                term_vals["foreign_amount"] = line.compute_line_amount(
                    base_amount_currency,
                    residual_amount_currency,
                    currency.decimal_places,
                )
                if cash_rounding:
                    difference = cash_rounding.compute_difference(
                        currency, term_vals["foreign_amount"]
                    )
                    if not currency.is_zero(difference):
                        term_vals["foreign_amount"] += difference
                        term_vals["company_amount"] = (
                            company_currency.round(term_vals["foreign_amount"] / rate)
                            if rate
                            else 0.0
                        )
            residual_amount -= term_vals["company_amount"]
            residual_amount_currency -= term_vals["foreign_amount"]
        return pay_term
