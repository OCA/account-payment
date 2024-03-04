# Copyright 2022 ForgeFlow, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    payment_line_id = fields.Many2one(
        "account.payment.counterpart.line", string="Payment line", ondelete="set null"
    )
