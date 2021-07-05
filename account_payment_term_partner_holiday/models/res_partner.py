# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"

    holiday_ids = fields.One2many(
        comodel_name="res.partner.holiday",
        inverse_name="partner_id",
        string="Payment Terms Holidays",
        copy=True,
        auto_join=True,
    )

    def is_date_in_holiday(self, date):
        if isinstance(date, str):
            date = fields.Date.from_string(date)
        res = self.holiday_ids.filtered(
            lambda x: int(x.month_from) <= date.month
            and int(x.month_to) >= date.month
            and int(x.day_from) <= date.day
            and int(x.day_to) >= date.day
        )
        if bool(res):
            res = res[0]
            res_date_to = False
            day_to = int(res.day_to)
            while not res_date_to:
                try:
                    res_date_to = fields.Date.from_string(
                        "%s-%s-%s" % (date.year, res.month_to, day_to)
                    )
                except ValueError:
                    day_to -= 1
            return [
                fields.Date.from_string(
                    "%s-%s-%s" % (date.year, res.month_from, res.day_from)
                ),
                res_date_to,
            ]
        return False


class ResPartnerHoliday(models.Model):
    _name = "res.partner.holiday"
    _description = "Partner Holidays"
    _order = "month_from, day_from, id"

    @api.model
    def _selection_days(self):
        return [(str(i), str(i)) for i in range(1, 32)]

    @api.model
    def _selection_months(self):
        return [
            ("1", _("January")),
            ("2", _("February")),
            ("3", _("March")),
            ("4", _("April")),
            ("5", _("May")),
            ("6", _("June")),
            ("7", _("July")),
            ("8", _("August")),
            ("9", _("September")),
            ("10", _("October")),
            ("11", _("November")),
            ("12", _("December")),
        ]

    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Partner",
        required=True,
        ondelete="cascade",
        index=True,
        copy=False,
    )
    day_from = fields.Selection(
        selection="_selection_days", string="Day from", required=True,
    )
    month_from = fields.Selection(
        selection="_selection_months", string="Month from", required=True,
    )
    day_to = fields.Selection(
        selection="_selection_days", string="Day to", required=True,
    )
    month_to = fields.Selection(
        selection="_selection_months", string="Month to", required=True,
    )

    @api.constrains("day_from", "month_from", "day_to", "month_to")
    def _check_from_end_dates(self):
        for item in self:
            if (int(item.month_from) > int(item.month_to)) or (
                int(item.month_to) == int(item.month_from)
                and int(item.day_from) > int(item.day_to)
            ):
                raise ValidationError(
                    _("You can't set the ending holidays period before the beginning.")
                )
