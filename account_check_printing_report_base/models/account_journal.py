# -*- coding: utf-8 -*-
# Copyright 2017 Tecnativa.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    check_print_auto = fields.Boolean(
        string='Automatic check printing',
        help='Default check for the company is printed automatically when '
             'invoice payment is validated',
    )
