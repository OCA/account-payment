# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    check_date = fields.Date(
        string="Check Date",
        default=fields.Date.context_today,
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        copy=False,
    )
