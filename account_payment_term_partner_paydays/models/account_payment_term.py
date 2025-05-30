# Copyright 2025 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


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
                return self._get_payment_days_due_date(date, decoded_payment_days)
        return super().apply_payment_days(line, date)
