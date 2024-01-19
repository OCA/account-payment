# Copyright 2024 Alexandre D. Díaz - Grupo Isonor

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    invoice_portal_confirmation_sign = fields.Boolean(
        related="company_id.invoice_portal_confirmation_sign",
        string="Online Signature",
        readonly=False,
    )
