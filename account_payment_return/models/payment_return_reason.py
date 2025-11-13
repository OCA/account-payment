# Copyright 2016 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.fields import Domain


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
        domain = Domain.TRUE if operator in Domain.NEGATIVE_OPERATORS else Domain.FALSE
        for f_name in self._rec_names_search:
            cond = Domain(f_name, operator, value)
            if operator in Domain.NEGATIVE_OPERATORS:
                domain &= cond
            else:
                domain |= cond
        return domain
