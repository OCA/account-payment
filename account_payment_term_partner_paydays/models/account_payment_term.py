# Copyright 2025 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


import calendar

from dateutil.relativedelta import relativedelta

from odoo import models


class AccountPaymentTerm(models.Model):
    _inherit = "account.payment.term"

    def _get_payment_days_due_date(self, date, payment_days):
        """Return the first configured payment day on or after ``date``."""
        if not payment_days:
            return date
        payment_days.sort()
        days_in_month = calendar.monthrange(date.year, date.month)[1]
        for day in payment_days:
            if date.day <= day:
                return date + relativedelta(day=min(day, days_in_month))
        day = min(payment_days[0], days_in_month)
        return date + relativedelta(day=day, months=1)

    def apply_payment_days(self, line, date):
        """Calculate the new date taking into account the partner payment days"""
        partner_id = self.env.context.get("partner_id")
        if partner_id:
            partner = self.env["res.partner"].browse(partner_id)
            payment_days = partner._get_payment_days()
            if payment_days:
                decoded_payment_days = line._decode_payment_days(payment_days)
                return self._get_payment_days_due_date(date, decoded_payment_days)
        return super().apply_payment_days(line, date)
