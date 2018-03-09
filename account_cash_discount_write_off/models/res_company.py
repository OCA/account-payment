# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):

    _inherit = 'res.company'

    default_cash_discount_writeoff_account_id = fields.Many2one(
        comodel_name='account.account',
        string="Cash Discount Write-Off Account"
    )
    default_cash_discount_writeoff_journal_id = fields.Many2one(
        comodel_name='account.journal',
        string="Cash Discount Write-Off Journal"
    )
