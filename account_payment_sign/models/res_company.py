# Copyright 2024 Alexandre D. Díaz - Grupo Isonor

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    invoice_portal_confirmation_sign = fields.Boolean(
        string="Invoice Online Signature", default=True
    )
