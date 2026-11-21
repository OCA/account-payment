# Copyright 2026 Jarsa
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    early_payment_percent = fields.Float(
        string="Early Payment Discount (%)",
        digits=(5, 2),
        help="Discount the supplier grants when its bills are paid within the "
        "early payment days.",
    )
    early_payment_percent_2 = fields.Float(
        string="Second Early Payment Discount (%)",
        digits=(5, 2),
        help="Some suppliers grant a second discount on top of the first one. "
        "It applies to what is left after the first: 2 and then 1 take "
        "2.98, not 3.",
    )
    early_payment_days = fields.Integer(
        help="Days to pay within to earn the discount.",
    )
    early_payment_base = fields.Selection(
        [("invoice", "Invoice Date"), ("receipt", "Receipt Date")],
        string="Early Payment Counted From",
        default="invoice",
    )

    def _early_payment_ratio(self):
        """Share of a bill the early payment takes off, both discounts chained."""
        self.ensure_one()
        kept = (1 - self.early_payment_percent / 100.0) * (
            1 - self.early_payment_percent_2 / 100.0
        )
        return 1 - kept
