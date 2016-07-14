# -*- coding: utf-8 -*-
# © 2015 Eficent Business and IT Consulting Services S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp import api, fields, models, _
import datetime
from lxml import etree


class AccountDaysOverdue(models.Model):
    _name = 'account.overdue.term'
    _description = 'Account Overdue Term'

    name = fields.Char(size=10, required=True)
    from_day = fields.Integer(string='From day', required=True)
    to_day = fields.Integer(string='From day', required=True)
    tech_name = fields.Char('Technical name', readonly=True)
