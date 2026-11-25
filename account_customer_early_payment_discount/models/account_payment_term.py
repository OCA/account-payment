# Copyright 2026 Jarsa
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class AccountPaymentTerm(models.Model):
    _inherit = "account.payment.term"

    early_discount_credit_note = fields.Boolean(
        string="Settle with a Credit Note",
        help="The discount is granted with a credit note applied to the "
        "invoice once the customer pays in time, instead of being written "
        "off when the payment is registered.",
    )
    early_discount_business_days = fields.Boolean(
        string="Count Business Days",
        help="The days to pay within are business days of the working "
        "calendar of the company: weekends and holidays do not count.",
    )
    early_discount_goods_only = fields.Boolean(
        string="On Goods Only",
        help="The discount leaves out the services of the invoice, such as "
        "freight or insurance, and takes off the goods only.",
    )

    def _compute_terms(self, *args, **kwargs):
        # The native discount is written off in the payment; here the credit
        # note settles it, so the payment must be for the full amount.
        res = super()._compute_terms(*args, **kwargs)
        if self.early_discount_credit_note:
            res.update(discount_percentage=0.0, discount_date=False, discount_balance=0)
            res.pop("discount_amount_currency", None)
        return res
