# -*- coding: utf-8 -*-
# © 2017 Carlos Dauden <carlos.dauden@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models


class PaymentReturnLine(models.Model):
    _inherit = 'account.journal'

    payment_return_pattern = fields.Char(
        string='Payment Return Ref Pattern',
        help='Pattern applied to reference in bank payment line search\n'
             'If empty takes complete reference',
    )
