# Copyright 2022 Coop IT Easy SCRLfs
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    is_customer_wallet_journal = fields.Boolean(
        string="Customer Wallet Journal", default=False
    )
