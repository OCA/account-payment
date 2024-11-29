# Copyright 2024 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    register_vendor_payment_state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("posted", "Posted"),
        ],
        string="Register Vendor Payment to State",
        default="posted",
        help="Default state for Register Payment (Outbound)",
    )
    register_customer_payment_state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("posted", "Posted"),
        ],
        string="Register Customer Payment to State",
        default="posted",
        help="Default state for Register Payment (Inbound)",
    )
