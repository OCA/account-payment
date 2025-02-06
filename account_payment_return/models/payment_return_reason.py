# Copyright 2016 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PaymentReturnReason(models.Model):
    _name = "payment.return.reason"
    _description = "Payment return reason"
    _rec_names_search = ["name", "code"]

    code = fields.Char()
    name = fields.Char(string="Reason", translate=True)
    display_name = fields.Char(compute="_compute_display_name")

    @api.depends("code", "name")
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"[{record.code}] {record.name}"
