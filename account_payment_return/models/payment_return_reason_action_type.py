# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PaymentReturnReasonActionType(models.Model):

    _name = "payment.return.reason.action.type"
    _description = "Payment Return Reason Action Types"
    _order = "sequence, id"

    name = fields.Char(required=True)
    sequence = fields.Integer("Sequence", default=10)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company",
        "Company",
        default=lambda self: self.env.user.company_id,
        ondelete="cascade",
    )
