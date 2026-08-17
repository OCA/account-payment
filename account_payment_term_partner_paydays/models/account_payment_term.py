# Copyright 2025 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import calendar

from dateutil.relativedelta import relativedelta

from odoo import models


class AccountPaymentTerm(models.Model):
    _inherit = "account.payment.term"

    def apply_payment_days(self, line, date):
        """Calculate the new date taking into account the partner payment days"""
        partner_id = self.env.context.get("partner_id")
        if partner_id:
            partner = self.env["res.partner"].browse(partner_id)
            payment_days = partner._get_payment_days()
            if payment_days:
                decoded_payment_days = line._decode_payment_days(payment_days)

                if decoded_payment_days:
                    new_date = None
                    decoded_payment_days.sort()
                    days_in_month = calendar.monthrange(date.year, date.month)[1]

                    for day in decoded_payment_days:
                        if date.day <= day:
                            if day > days_in_month:
                                day = days_in_month
                            new_date = date + relativedelta(day=day)
                            break
                    if not new_date:
                        day = decoded_payment_days[0]
                        if day > days_in_month:
                            day = days_in_month
                        new_date = date + relativedelta(day=day, months=1)
                    return new_date
        return super().apply_payment_days(line, date)
