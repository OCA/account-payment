# Copyright 2023 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import json

from lxml import etree

from odoo import api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.model
    def fields_view_get(
        self, view_id=None, view_type="form", toolbar=False, submenu=False
    ):
        res = super().fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu
        )
        group = "account_payment_term_security.account_payment_term_mgmt"
        if view_type == "form":
            doc = etree.XML(res["arch"])
            for node in doc.xpath("//field[@name='payment_term_id']"):
                if not self.env.user.has_group(group):
                    node.set("readonly", "1")
                    node.set("force_save", "1")
                    modifiers = json.loads(node.get("modifiers"))
                    modifiers["readonly"] = True
                    modifiers["force_save"] = 1
                    node.set("modifiers", json.dumps(modifiers))
            res["arch"] = etree.tostring(doc, encoding="unicode")
        return res
