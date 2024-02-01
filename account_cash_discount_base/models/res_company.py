# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ResCompany(models.Model):

    _inherit = "res.company"

    cash_discount_base_amount_type = fields.Selection(
        selection="_get_cash_discount_base_amount_types",
        required=True,
        default="untaxed",
    )
    cash_discount_use_tax_adjustment = fields.Boolean(
        compute="_compute_cash_discount_tax_adjustment",
        store=True,
    )

    early_pay_discount_computation = fields.Selection(
        inverse="_inverse_early_pay_discount_computation",
    )

    @api.model
    def _get_cash_discount_base_amount_types(self):
        return [
            ("untaxed", _("Excluding tax")),
            ("total", _("Including all taxes")),
        ]

    @api.depends(
        "cash_discount_base_amount_type",
    )
    def _compute_cash_discount_tax_adjustment(self):
        for rec in self:
            rec.cash_discount_use_tax_adjustment = (
                rec.cash_discount_base_amount_type == "total"
            )

    @api.constrains("early_pay_discount_computation")
    def _check_early_pay_discount_computation(self):
        if any(rec.early_pay_discount_computation == "mixed" for rec in self):
            raise UserError(
                _(
                    "Option Cash Discount Tax Reduction:"
                    " 'Always (upon invoice)' is not supported"
                )
            )

    @api.depends("cash_discount_base_amount_type")
    def _compute_early_pay_discount_computation(self):
        """
        @override: value is directly dependent to cash_discount_base_amount_type
        """
        for company in self:
            if company.cash_discount_base_amount_type == "total":
                company.early_pay_discount_computation = "included"
            elif company.cash_discount_base_amount_type == "untaxed":
                company.early_pay_discount_computation = "excluded"
            else:
                # shouldn't happen
                company.early_pay_discount_computation = "excluded"

    def _inverse_early_pay_discount_computation(self):
        for company in self:
            if company.early_pay_discount_computation == "included":
                company.cash_discount_base_amount_type = "total"
            elif company.early_pay_discount_computation == "excluded":
                company.cash_discount_base_amount_type = "untaxed"
            else:
                # shouldn't happen: if 'mixed', an error is raised
                company.cash_discount_base_amount_type = "untaxed"
