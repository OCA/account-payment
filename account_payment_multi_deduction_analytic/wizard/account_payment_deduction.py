# Copyright 2021 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models, api


class AccountPaymentDeduction(models.TransientModel):
    _inherit = "account.payment.deduction"

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
