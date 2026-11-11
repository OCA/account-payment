# Copyright 2024 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    payment_terms_delay_type = fields.Selection(
        string="Payment terms Delay types",
        default="days",
        selection=[
            ("days", "Days"),
            ("weeks", "Days and Weeks"),
            ("months", "Days and Months"),
            ("weeks_and_months", "Days, Weeks and Months"),
        ],
        help="Choose the type of delay when creating new payment terms.",
    )
