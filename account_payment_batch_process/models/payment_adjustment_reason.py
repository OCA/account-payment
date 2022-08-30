# Copyright (C) 2021, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PaymentAdjustmentReason(models.Model):
    _name = "payment.adjustment.reason"
    _rec_name = "code"
    _description = "Payment Adjustment Reason"

    code = fields.Char(required=True, copy=False)
    account_id = fields.Many2one("account.account")
    reason = fields.Text(copy=False)

    def name_get(self):
        result = []
        for pay in self:
            result.append((pay.id, "%s" % (pay.code or "")))
        return result
