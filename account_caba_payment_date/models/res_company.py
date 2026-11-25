# Copyright 2026 Jarsa (https://www.jarsa.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    caba_payment_date_lock_policy = fields.Selection(
        [
            ("block", "Block the reconciliation"),
            ("next_open", "Use the first open date"),
            ("standard", "Keep the standard behavior"),
        ],
        default="block",
        required=True,
        string="Cash Basis Lock Policy",
        help="What to do when the payment date of a cash basis entry falls in a "
        "locked period:\n"
        "- Block the reconciliation: raise an error asking to reopen the period.\n"
        "- Use the first open date: date the entry on the first day after the lock.\n"
        "- Keep the standard behavior: let Odoo date the entry on the "
        "reconciliation date.",
    )
