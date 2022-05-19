# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AccountPaymentTerm(models.Model):
    _inherit = "account.payment.term"

    @api.one
    def compute(self, value, date_ref=False):
        """Compute the due date taking into account the holiday periods
        set in the partner.

        Once an initial date resulting of the payment term is computed,
        compute the first available date after that.
        Then, apply_payment_days() and apply_holidays() to prevent
        incompatibilities.
        """
        result = super().compute(value=value, date_ref=date_ref)[0]
        ctx = self.env.context
        partner_id = ctx.get("move_partner_id", ctx.get("default_partner_id"))
        if partner_id:
            partner = self.env["res.partner"].browse(partner_id)
            result2 = []
            for key, item in enumerate(result):
                next_date = partner._get_valid_due_date(item[0])
                if next_date != item[0]:
                    line = self.line_ids[key]
                    next_date = self.apply_payment_days(line, next_date)
                    next_date = self.apply_holidays(next_date)
                    result2.append((fields.Date.to_string(next_date), item[1]))
                else:
                    result2.append(item)
            result = result2
        return result
