# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import fields, models


class AccountInvoiceLine(models.Model):

    _inherit = 'account.invoice.line'

    is_cash_discount_tax = fields.Boolean(
        help="Technical field that helps to know which are lines generated"
             "for cash discount on taxes",
    )
