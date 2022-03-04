# Copyright 2020 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import _, api, fields, models


class AccountPaymentDeduction(models.TransientModel):
    _name = "account.payment.deduction"
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
    open = fields.Boolean(help="Keep this line open")
    amount = fields.Monetary(string="Deduction Amount", required=True)
    name = fields.Char(string="Label", required=True)
    analytic_account_id = fields.Many2one(
        comodel_name="account.analytic.account",
        string="Analytic Account",
        compute="_compute_analytic_multi_deduction",
        readonly=False,
        store=True,
        index=True,
    )
    analytic_tag_ids = fields.Many2many(
        comodel_name="account.analytic.tag",
        string="Analytic Tags",
    )

    @api.depends("payment_id")
    def _compute_analytic_multi_deduction(self):
        for rec in self:
            rec.analytic_account_id = rec.payment_id.deduct_analytic_account_id
            rec.analytic_tag_ids = rec.payment_id.deduct_analytic_tag_ids

    @api.onchange("open")
    def _onchange_open(self):
        if self.open:
            self.account_id = False
            self.name = _("Keep open")
        else:
            self.name = False

    @api.onchange("account_id")
    def _onchange_account_id(self):
        if self.account_id:
            self.open = False
