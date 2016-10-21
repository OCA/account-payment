# -*- coding: utf-8 -*-
# © 2015 Eficent Business and IT Consulting Services S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp import fields, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    aging_comments = fields.Text(string='Aging comments')
