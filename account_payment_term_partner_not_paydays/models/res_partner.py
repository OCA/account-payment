# Copyright 2025 Binhex <https://www.binhex.cloud>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    partner_not_pay_ids = fields.One2many("res.partner.not.pay", "partner_id")
    days_not_pay = fields.Boolean(compute="_compute_days_not_pay")

    def _get_payment_days(self):
        move_type = self.env.context.get("move_type")
        if move_type in ("in_invoice", "in_refund", "in_receipt"):
            return self.supplier_payment_days
        if move_type in ("out_invoice", "out_refund", "out_receipt"):
            return self.customer_payment_days
        return super()._get_payment_days()

    def _compute_days_not_pay(self):
        IrConfigParameter = self.env["ir.config_parameter"]
        for partner in self:
            partner.days_not_pay = IrConfigParameter.get_param(
                "account_payment_term_partner_not_paydays.days_not_pay"
            )

    def _get_domain_range_not_pay(self, **args):
        domain = [
            ("partner_id", "=", self.id),
        ]
        compare_date = args.get("compare_date", False)
        if compare_date:
            domain += [
                ("date_start", "<=", compare_date),
                ("date_end", ">=", compare_date),
            ]

        move_type = args.get("move_type", False)
        if move_type:
            domain += [("type", "=", move_type)]
        return domain

    def _get_fields_range_not_pay(self):
        return ["date_start", "date_end"]

    def _check_partner_range_not_pay(self, **args):
        self.ensure_one()
        overlap = self.env["res.partner.not.pay"].search_read(
            self._get_domain_range_not_pay(**args),
            self._get_fields_range_not_pay(),
            limit=1,
        )
        return overlap
