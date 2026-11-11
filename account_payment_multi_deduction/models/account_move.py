# Copyright 2025 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    is_writeoff = fields.Boolean()
