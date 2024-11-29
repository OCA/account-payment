# Copyright 2024 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    register_vendor_payment_state = fields.Selection(
        related="company_id.register_vendor_payment_state",
        string="Register Vendor Payment to State",
        readonly=False,
        help="Default state for Register Payment (Outbound)",
    )
    register_customer_payment_state = fields.Selection(
        related="company_id.register_customer_payment_state",
        string="Register Customer Payment to State",
        readonly=False,
        help="Default state for Register Payment (Inbound)",
    )
