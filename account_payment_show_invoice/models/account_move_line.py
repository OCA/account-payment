# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountMoveLine(models.Model):

    _inherit = 'account.move.line'

    payment_invoice_ids = fields.Many2many(
        string="Payment Invoices",
        related='payment_id.invoice_ids',
        readonly=True,
    )
