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
        holiday = self.holiday_ids.search(
            [("payment_id", "=", self.id), ("holiday", "=", date)]
        )
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
                        if day > days_in_month:
                            day = days_in_month
                        new_date = date + relativedelta(day=day)
                        break
                if not new_date:
                    day = payment_days[0]
                    if day > days_in_month:
                        day = days_in_month
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
        "early_discount",
        "discount_percentage",
        "discount_days",
        "sequential_lines",
        "holiday_ids",
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
        """Complete overwrite of compute method for adding extra options."""
        if cash_rounding:
            raise UserError(
                self.env._("This module is not compatible with cash rounding")
            )
        # FIXME: Find an inheritable way of doing this
        self.ensure_one()
        company_currency = company.currency_id
        total_amount = remaining_amount = tax_amount + untaxed_amount
        total_amount_currency = remaining_amount_currency = (
            tax_amount_currency + untaxed_amount_currency
        )
        pay_term = {
            "total_amount": total_amount,
            "discount_percentage": self.discount_percentage
            if self.early_discount
            else 0.0,
            "discount_date": date_ref + relativedelta(days=(self.discount_days or 0))
            if self.early_discount
            else False,
            "discount_balance": 0,
            "line_ids": [],
        }

        if self.early_discount:
            # Early discount is only available on single line, 100% payment terms.
            discount_percentage = self.discount_percentage / 100.0
            if self.early_pay_discount_computation in ("excluded", "mixed"):
                pay_term["discount_balance"] = company_currency.round(
                    total_amount - untaxed_amount * discount_percentage
                )
                pay_term["discount_amount_currency"] = currency.round(
                    total_amount_currency
                    - untaxed_amount_currency * discount_percentage
                )
            else:
                pay_term["discount_balance"] = company_currency.round(
                    total_amount * (1 - discount_percentage)
                )
                pay_term["discount_amount_currency"] = currency.round(
                    total_amount_currency * (1 - discount_percentage)
                )

        residual_amount = total_amount
        residual_amount_currency = total_amount_currency
        precision_digits = currency.decimal_places
        company_precision_digits = company_currency.decimal_places
        next_date = date_ref
        for i, line in enumerate(self.line_ids):
            if not self.sequential_lines:
                # For all lines, the beginning date is `date_ref`
                next_date = line._get_due_date(date_ref)
            else:
                next_date = line._get_due_date(next_date)

            next_date = self.apply_payment_days(line, next_date)
            next_date = self.apply_holidays(next_date)

            term_vals = {
                "date": next_date,
                "company_amount": 0,
                "foreign_amount": 0,
            }

            if i == len(self.line_ids) - 1:
                # The last line is always the balance, no matter the type
                term_vals["company_amount"] = residual_amount
                term_vals["foreign_amount"] = residual_amount_currency
            elif line.value == "fixed":
                # Fixed amounts
                line_amount = line.compute_line_amount(
                    total_amount, remaining_amount, precision_digits
                )
                company_line_amount = line.compute_line_amount(
                    total_amount, remaining_amount, company_precision_digits
                )
                term_vals["company_amount"] = sign * company_line_amount
                term_vals["foreign_amount"] = sign * line_amount
            elif line.value == "percent_amount_untaxed":
                if company_currency != currency:
                    raise UserError(
                        self.env._(
                            "Percentage of amount untaxed can't be used with foreign "
                            "currencies"
                        )
                    )
                line_amount = line.compute_line_amount(
                    untaxed_amount, untaxed_amount, precision_digits
                )
                company_line_amount = line.compute_line_amount(
                    untaxed_amount_currency,
                    untaxed_amount_currency,
                    company_precision_digits,
                )
                term_vals["company_amount"] = company_line_amount
                term_vals["foreign_amount"] = line_amount
            else:
                # Percentage amounts
                line_amount = line.compute_line_amount(
                    total_amount, remaining_amount, precision_digits
                )
                company_line_amount = line.compute_line_amount(
                    total_amount_currency,
                    remaining_amount_currency,
                    company_precision_digits,
                )
                term_vals["company_amount"] = company_line_amount
                term_vals["foreign_amount"] = line_amount

            residual_amount -= term_vals["company_amount"]
            residual_amount_currency -= term_vals["foreign_amount"]
            pay_term["line_ids"].append(term_vals)

        return pay_term
