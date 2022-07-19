# Copyright 2021 Tecnativa - Víctor Martínez
# Copyright 2021 Tecnativa - João Marques
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import calendar

from dateutil.relativedelta import relativedelta

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

    def _get_valid_due_date(self, date):
        if isinstance(date, str):
            date = fields.Date.from_string(date)
        is_date_in_holiday = self.is_date_in_holiday(date)
        while is_date_in_holiday:
            date = is_date_in_holiday[1] + relativedelta(days=1)
            is_date_in_holiday = self.is_date_in_holiday(date)
        return date

    def is_date_in_holiday(self, date):
        if isinstance(date, str):
            date = fields.Date.from_string(date)
        for holiday in self.commercial_partner_id.holiday_ids:
            holiday_start_date = self._generate_field_date(
                date.year, int(holiday.month_from), int(holiday.day_from)
            )
            holiday_end_date = self._generate_field_date(
                date.year, int(holiday.month_to), int(holiday.day_to)
            )
            if date >= holiday_start_date and date <= holiday_end_date:
                return [holiday_start_date, holiday_end_date]
        return False

    def _generate_field_date(self, year, month, day):
        # When the user selects a date that does not exist, assume the last day
        # for that month
        days = (day, max(calendar.monthrange(year, month)))
        return fields.Date.from_string("%s-%s-%s" % (year, month, min(days)))


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
            ("01", _("January")),
            ("02", _("February")),
            ("03", _("March")),
            ("04", _("April")),
            ("05", _("May")),
            ("06", _("June")),
            ("07", _("July")),
            ("08", _("August")),
            ("09", _("September")),
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
        selection="_selection_days",
        required=True,
    )
    month_from = fields.Selection(
        selection="_selection_months",
        required=True,
    )
    day_to = fields.Selection(
        selection="_selection_days",
        required=True,
    )
    month_to = fields.Selection(
        selection="_selection_months",
        required=True,
    )

    _sql_constraints = [
        (
            "month_consistency",
            "CHECK(month_from <= month_to)",
            "Month from should be higher than month from",
        ),
    ]

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
