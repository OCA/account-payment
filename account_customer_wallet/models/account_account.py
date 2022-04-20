# Copyright 2022 Coop IT Easy SCRLfs
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class Account(models.Model):
    _inherit = "account.account"

    # TODO: Figure out whether there already exists a module that makes this
    # One2many field available
    move_line_ids = fields.One2many(
        comodel_name="account.move.line",
        inverse_name="account_id",
        string="Account Move Lines",
    )
