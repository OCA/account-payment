# Copyright 2025 Spearhead - Ricardo Jara
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class AccountPayment(models.Model):
    _name = "account.payment"
    _inherit = ["account.payment", "tier.validation"]
    _state_from = ["draft"]
    _state_to = ["in_process", "paid"]
    _cancel_state = "canceled"

    _tier_validation_manual_config = False
