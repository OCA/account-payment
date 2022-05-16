# Copyright 2016 ForgeFlow S.L.
#   (<http://www.forgeflow.com>).
# Copyright 2016 Therp BV (<http://therp.nl>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, api, exceptions, fields, models
from odoo.modules.registry import Registry


class AccountDaysOverdue(models.Model):
    _name = "account.overdue.term"
    _description = "Account Overdue Term"

    name = fields.Char(size=10, required=True)
    from_day = fields.Integer(string="From day", required=True)
    to_day = fields.Integer(string="To day", required=True)
    tech_name = fields.Char(
        string="Technical name",
        readonly=True,
        compute="_compute_technical_name",
        store=True,
    )

    @api.depends("from_day", "to_day")
    def _compute_technical_name(self):
        for rec in self:
            rec.tech_name = "overdue_term_%d_%d" % (rec.from_day, rec.to_day)

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if self.env["account.move.line"]._register_hook():
            Registry(self.env.cr.dbname).registry_invalidated = True
        return res

    def write(self, vals):
        res = super().write(vals)
        if self.env["account.move.line"]._register_hook():
            Registry(self.env.cr.dbname).registry_invalidated = True
        return res

    @api.constrains("from_day", "to_day")
    def check_overlap(self):
        """Check that overdue terms do not overlap"""
        for rec in self:
            date_domain = [
                ("from_day", "<=", rec.to_day),
                ("to_day", ">=", rec.from_day),
                ("id", "!=", self.id),
            ]
            overlap = self.search(date_domain)
            if overlap:
                raise exceptions.ValidationError(
                    _("Overdue Term %s overlaps with %s")
                    % (rec.name, fields.first(overlap).name)
                )
