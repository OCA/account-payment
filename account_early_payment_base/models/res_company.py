# Copyright 2026 Jarsa
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from datetime import datetime, time, timedelta

import pytz

from odoo import models


class ResCompany(models.Model):
    _inherit = "res.company"

    def _early_payment_calendar(self):
        """Working hours of the company, the ones that tell a business day."""
        self.ensure_one()
        return self.resource_calendar_id or self.env["resource.calendar"].search(
            [("company_id", "in", [self.id, False])], limit=1
        )

    def _add_business_days(self, start, days):
        """Date `days` business days after `start`.

        A business day is a day the working calendar of the company has hours
        on, so its holidays are skipped along with the weekends. `start`
        itself never counts as one of the days.
        """
        self.ensure_one()
        calendar = self._early_payment_calendar()
        if not calendar:
            return start + timedelta(days=days)
        begin = pytz.timezone(calendar.tz).localize(
            datetime.combine(start + timedelta(days=1), time.min)
        )
        return calendar.plan_days(days, begin, compute_leaves=True).date()

    def _is_business_day(self, date):
        self.ensure_one()
        return self._add_business_days(date - timedelta(days=1), 1) == date
