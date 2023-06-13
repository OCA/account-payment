# Copyright 2016 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PaymentReturnReason(models.Model):
    _name = "payment.return.reason"
    _description = "Payment return reason"
    _rec_names_search = ["name", "code"]

    code = fields.Char()
    name = fields.Char(string="Reason", translate=True)

    def name_get(self):
        return [
            (r.id, "[{code}] {name}".format(code=r.code, name=r.name)) for r in self
        ]
