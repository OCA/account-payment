# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):

    _inherit = "res.config.settings"

    account_payment_return_threshold = fields.Integer(
        related="company_id.account_payment_return_threshold",
        readonly=False,
        string="Payment Return Threshold",
    )
