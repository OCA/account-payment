# Copyright 2022 Coop IT Easy SCRL fs
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class Company(models.Model):
    _inherit = "res.company"

    customer_wallet_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Customer Wallet Account",
        # TODO: Filter domain on type?
    )
