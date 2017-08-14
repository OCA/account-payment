# -*- coding: utf-8 -*-
# Copyright 2017 luis M. Ontalba <luis.martinez@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    default_expense_account_id = fields.Many2one(
        comodel_name='account.account', string='Default Expense Account',
        help='Default account for commission expenses')
    default_expense_partner_id = fields.Many2one(
        comodel_name="res.partner", string="Default Expense Partner",
        domain=[('supplier', '=', True)], help='Default partner for '
                                               'commission expenses')
