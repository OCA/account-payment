# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class AccountConfigSettings(models.TransientModel):

    _inherit = 'account.config.settings'

    enable_cash_discount_tax = fields.Boolean(
        related='company_id.enable_cash_discount_tax',
        help='Check this to enable Cash Discount for Tax Button',
    )
    cash_discount_tax_description = fields.Char(
        related='company_id.cash_discount_tax_description',
        string='Cash Discount Description for Taxes Lines',
        help="The description used in invoices when generating cash discount"
             "lines for taxes",
        translate=True,
    )
    cash_discount_tax_account_id = fields.Many2one(
        related='company_id.cash_discount_tax_account_id',
        string='Cash Discount Account for Taxes Lines',
        help="The account used in invoices when generating cash discount"
             "lines for taxes"
    )
    cash_discount_invoice_tax = fields.Boolean(
        related='company_id.cash_discount_invoice_tax',
        string="Tax discount on invoice basis",
        help="When checked, generate tax discount invoice lines on resultant"
             "invoice taxes instead of invoice line taxes (as group taxes can"
             "be chosen on lines level)"
    )
