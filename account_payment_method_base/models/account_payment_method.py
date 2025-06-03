# Copyright 2025 Akretion France (https://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AccountPaymentMethod(models.Model):
    _inherit = "account.payment.method"
    _order = "code, payment_type"  # no native _order
    _rec_names_search = ["name", "code"]

    # Add the one2many field, which should be native but is missing
    # in the 'account' module
    line_ids = fields.One2many(
        comodel_name="account.payment.method.line",
        inverse_name="payment_method_id",
        string="Payment Methods",
    )

    @api.depends("code", "name", "payment_type")
    def _compute_display_name(self):
        paytype2label = dict(
            self.fields_get("payment_type", "selection")["payment_type"]["selection"]
        )
        for method in self:
            display_name = (
                f"[{method.code}] {method.name} ({paytype2label[method.payment_type]})"
            )
            method.display_name = display_name
