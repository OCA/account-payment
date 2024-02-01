# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountPaymentTerm(models.Model):

    _inherit = "account.payment.term"

    discount_percent = fields.Float(
        string="Discount (%)",
        digits="Discount",
        compute="_compute_discount_percent",
    )
    discount_delay = fields.Integer(
        string="Discount Delay (days)", compute="_compute_discount_delay"
    )

    @api.depends("line_ids.discount_percentage")
    def _compute_discount_percent(self):
        for rec in self:
            rec.discount_percent = fields.first(rec.line_ids).discount_percentage or 0.0

    @api.depends("line_ids.discount_days")
    def _compute_discount_delay(self):
        for rec in self:
            rec.discount_delay = fields.first(rec.line_ids).discount_days or 0

    @api.constrains("line_ids")
    def check_discount(self):
        if any(rec.discount_percent and len(rec.line_ids) > 1 for rec in self):
            raise UserError(
                _("You cannot have multiple lines on payment term with discount")
            )
