# Copyright 2026 Jarsa (https://www.jarsa.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    caba_payment_date_lock_policy = fields.Selection(
        related="company_id.caba_payment_date_lock_policy",
        readonly=False,
    )
