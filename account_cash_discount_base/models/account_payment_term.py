# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountPaymentTerm(models.Model):

    _inherit = "account.payment.term"

    discount_percent = fields.Float(
        string="Discount (%)",
        digits="Discount",
    )
    discount_delay = fields.Integer(string="Discount Delay (days)")
