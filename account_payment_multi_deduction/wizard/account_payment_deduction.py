# Copyright 2020 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import _, api, fields, models


class AccountPaymentDeduction(models.TransientModel):
    _name = "account.payment.deduction"
    _inherit = "analytic.mixin"
    _description = "Payment Deduction"

    payment_id = fields.Many2one(
        comodel_name="account.payment.register",
        readonly=True,
        ondelete="cascade",
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        related="payment_id.currency_id",
        readonly=True,
    )
    account_id = fields.Many2one(
        comodel_name="account.account",
        domain=[("deprecated", "=", False)],
        required=False,
    )
    is_open = fields.Boolean(string="Open", help="Keep this line open")
    amount = fields.Monetary(string="Deduction Amount", required=True)
    name = fields.Char(string="Label", required=True)

    @api.onchange("is_open")
    def _onchange_open(self):
        if self.is_open:
            self.account_id = False
            self.name = _("Keep open")
        else:
            self.name = False

    @api.onchange("account_id")
    def _onchange_account_id(self):
        if self.account_id:
            self.is_open = False
