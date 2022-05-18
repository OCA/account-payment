# Copyright 2016 ForgeFlow S.L. (
#   (<http://www.forgeflow.com>).
# Copyright 2016 Therp BV (<http://therp.nl>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import datetime

from lxml import etree

from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    days_overdue = fields.Integer(
        compute="_compute_days_overdue",
        search="_search_days_overdue",
        string="Days overdue",
    )

    @api.depends("date_maturity")
    def _compute_days_overdue(self):
        today_date = fields.Date.from_string(fields.Date.today())
        for line in self:
            days = None
            if line.date_maturity and line.amount_residual:
                date_maturity = fields.Date.from_string(line.date_maturity)
                days_overdue = (today_date - date_maturity).days
                if days_overdue > 0:
                    days = days_overdue
            line.days_overdue = days

    def _search_days_overdue(self, operator, value):
        due_date = fields.Date.from_string(fields.Date.today()) - datetime.timedelta(
            days=value
        )
        if operator in ("!=", "<>", "in", "not in"):
            raise ValueError("Invalid operator: {}".format(operator))
        if operator == ">":
            operator = "<"
        elif operator == "<":
            operator = ">"
        elif operator == ">=":
            operator = "<="
        elif operator == "<=":
            operator = ">="
        return [("date_maturity", operator, due_date)]

    @api.depends("date_maturity")
    def _compute_overdue_terms(self):
        today_date = fields.Date.from_string(fields.Date.today())
        overdue_terms = self.env["account.overdue.term"].search([])
        for line in self:
            for term in overdue_terms:
                line[term.tech_name] = 0.0
            if line.date_maturity and line.amount_residual:
                date_maturity = fields.Date.from_string(line.date_maturity)
                days_overdue = (today_date - date_maturity).days

                for overdue_term in overdue_terms:
                    if (
                        overdue_term.to_day >= days_overdue >= overdue_term.from_day
                        and abs(line.amount_residual) > 0.0
                    ):
                        line[overdue_term.tech_name] = line.amount_residual

    @api.model
    def fields_view_get(
        self, view_id=None, view_type="form", toolbar=False, submenu=False
    ):
        result = super().fields_view_get(
            view_id,
            view_type,
            toolbar=toolbar,
            submenu=submenu,
        )

        doc = etree.XML(result["arch"])
        if view_type == "tree":
            for placeholder in doc.xpath("//field[@name='days_overdue']"):
                for overdue_term in self.env["account.overdue.term"].search(
                    [], order="from_day DESC"
                ):
                    elem = etree.Element(
                        "field",
                        {
                            "name": str(overdue_term.tech_name),
                            "readonly": "True",
                            "sum": "Total",
                        },
                    )
                    placeholder.addnext(elem)
                result["arch"] = etree.tostring(doc)
            xarch, xfields = self.env["ir.ui.view"].postprocess_and_fields(
                etree.fromstring(result["arch"]), self._name
            )
            result["arch"] = xarch
            result["fields"] = xfields
        return result

    @api.model
    def _add_terms(self, field_name, term_name):
        self._add_field(
            field_name, fields.Float(string=term_name, compute="_compute_overdue_terms")
        )
        return True

    def _register_hook(self):
        term_obj = self.env["account.overdue.term"]
        for term in term_obj.search([]):
            # the orm does unicode
            field_name = str(term.tech_name)
            # register_hook can be called multiple times
            if field_name in self._fields:
                continue
            self._add_terms(field_name, term.name)
        self._setup_fields()
        self._setup_complete()
        return super()._register_hook()
