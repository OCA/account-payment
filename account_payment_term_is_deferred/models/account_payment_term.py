# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountPaymentTerm(models.Model):
    _inherit = "account.payment.term"

    is_deferred = fields.Boolean(
        help="Check this if you want to identify this payment term as deferred."
    )
