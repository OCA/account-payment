# Copyright 2013-2016 Camptocamp SA (Yannick Vaucher)
# Copyright 2004-2016 Odoo S.A. (www.odoo.com)
# Copyright 2015-2016 Akretion
# (Alexis de Lattre <alexis.delattre@akretion.com>)
# Copyright 2018 Simone Rubino - Agile Business Group
# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AccountPaymentTermHoliday(models.Model):
    _name = "account.payment.term.holiday"
    _description = "Payment Term Holidays"

    payment_id = fields.Many2one(
        comodel_name="account.payment.term", ondelete="cascade"
    )
    holiday = fields.Date(required=True)
    date_postponed = fields.Date(string="Postponed date", required=True)

    @api.constrains("holiday", "date_postponed")
    def check_holiday(self):
        for record in self:
            if record.date_postponed <= record.holiday:
                raise ValidationError(
                    self.env._("Holiday %s can only be postponed into the future")
                    % record.holiday
                )
            if (
                record.search_count(
                    [
                        ("payment_id", "=", record.payment_id.id),
                        ("holiday", "=", record.holiday),
                    ]
                )
                > 1
            ):
                raise ValidationError(
                    self.env._("Holiday %s is duplicated in current payment term")
                    % record.holiday
                )
            if (
                record.search_count(
                    [
                        ("payment_id", "=", record.payment_id.id),
                        "|",
                        ("date_postponed", "=", record.holiday),
                        ("holiday", "=", record.date_postponed),
                    ]
                )
                >= 1
            ):
                raise ValidationError(
                    self.env._("Date %s cannot is both a holiday and a Postponed date")
                    % record.holiday
                )
