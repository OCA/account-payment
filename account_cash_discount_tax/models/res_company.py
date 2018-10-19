# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import fields, models


class AccountInvoice(models.Model):

    _inherit = 'res.company'

    cash_discount_tax_description = fields.Char(
        string='Description for Tax Discount',
        help="The description used in invoices when generating cash discount"
             "lines for taxes",
        translate=True,
    )
    cash_discount_tax_account_id = fields.Many2one(
        'account.account',
        string="Account for Tax Discount",
        help="The account used to add tax cash discount"
    )
    cash_discount_invoice_tax = fields.Boolean(
        string="Tax discount on invoice basis",
        help="When checked, generate tax discount invoice lines on resultant"
             "invoice taxes instead of invoice line taxes (as group taxes can"
             "be chosen on lines level)"
    )
