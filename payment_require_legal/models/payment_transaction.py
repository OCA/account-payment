# Copyright 2026 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    legal_terms_acceptance_metadata = fields.Text(readonly=True, copy=False)
