# Copyright 2020 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    def _is_sale_payment_managed(self):
        return self.env.user.has_group(
            "sales_team.group_sale_salesman"
        ) and not self.env.user.has_group("account.group_account_invoice")

    def post(self):
        obj = self
        if self._is_sale_payment_managed():
            obj = self.sudo()
        return super(AccountPayment, obj).post()

    @api.model
    def fields_view_get(
        self, view_id=None, view_type="form", toolbar=False, submenu=False
    ):
        result = super(AccountPayment, self).fields_view_get(
            view_id, view_type, toolbar=toolbar, submenu=submenu,
        )
        if view_type == "form":
            if self._is_sale_payment_managed():
                result["fields"]["partner_type"]["selection"] = [
                    ("customer", _("Customer"))
                ]
        return result
