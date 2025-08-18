# Copyright 2016 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.osv import expression


class PaymentReturnReason(models.Model):
    _name = "payment.return.reason"
    _description = "Payment return reason"
    _rec_names_search = ["name", "code"]

    code = fields.Char()
    name = fields.Char(string="Reason", translate=True)
    display_name = fields.Char(
        compute="_compute_display_name", search="_search_display_name"
    )

    @api.depends("code", "name")
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"[{record.code}] {record.name}"

    @api.model
    def _search_display_name(self, operator, value):
        domain = []
        for f_name in self._rec_names_search:
            domain_item = [(f_name, operator, value)]
            if domain == []:
                domain = domain_item
            else:
                if operator in expression.NEGATIVE_TERM_OPERATORS:
                    domain = expression.AND([domain, domain_item])
                else:
                    domain = expression.OR([domain, domain_item])
        return domain
