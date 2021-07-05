# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from dateutil.relativedelta import relativedelta

from odoo import fields, models


class AccountPaymentTerm(models.Model):
    _inherit = "account.payment.term"

    def compute(self, value, date_ref=False, currency=None):
        result = super().compute(value=value, date_ref=date_ref, currency=currency)
        ctx = self.env.context
        partner_id = ctx.get("move_partner_id", ctx.get("default_partner_id"))
        if partner_id:
            partner = self.env["res.partner"].browse(partner_id)
            result2 = []
            for item in result:
                date_item = item[0]
                is_date_in_holiday = partner.is_date_in_holiday(date_item)
                if is_date_in_holiday:
                    next_date = is_date_in_holiday[1]
                    next_date += relativedelta(days=1)
                    result2.append((fields.Date.to_string(next_date), item[1]))
                else:
                    result2.append(item)
            result = result2
        return result
