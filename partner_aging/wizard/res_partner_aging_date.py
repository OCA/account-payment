# Copyright 2012 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResPartnerAgingDate(models.TransientModel):
    _name = "res.partner.aging.date"
    _description = "Res Partner Aging Date"

    age_date = fields.Date(
        "Aging Date",
        required=True,
        default=lambda self: fields.Date.context_today(self),
    )

    def open_customer_aging(self):
        customer_aging = self.env["res.partner.aging.customer"]
        for res in self:
            ctx = self._context.copy()
            ctx.update({"age_date": res.age_date})
            customer_aging.execute_aging_query(age_date=res.age_date)
            action = self.env.ref("partner_aging.action_customer_aging_tree").read()[0]
            action["domain"] = [("total", "<>", 0.0000000)]
            action["context"] = ctx
            return action

    def open_supplier_aging(self):
        supplier_aging = self.env["res.partner.aging.supplier"]
        for res in self:
            ctx = self._context.copy()
            ctx.update({"age_date": res.age_date})
            supplier_aging.execute_aging_query(age_date=res.age_date)
            action = self.env.ref("partner_aging.action_supplier_aging_tree").read()[0]
            action["domain"] = [
                "|",
                "|",
                "|",
                "|",
                "|",
                "|",
                ("total", "<>", 0.000000),
                ("days_due_01to30", "<>", 0.000000),
                ("days_due_31to60", "<>", 0.000000),
                ("days_due_61to90", "<>", 0.000000),
                ("days_due_91to120", "<>", 0.000000),
                ("days_due_121togr", "<>", 0.000000),
                ("not_due", "<>", 0.000000),
            ]
            action["context"] = ctx
            return action
