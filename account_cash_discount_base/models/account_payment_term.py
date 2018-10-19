# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models
from odoo.addons import decimal_precision as dp


class AccountPaymentTerm(models.Model):

    _inherit = 'account.payment.term'

    discount_percent = fields.Float(
        string='Discount (%)',
        digits=dp.get_precision('Discount'),
    )
    discount_delay = fields.Integer(
        string='Discount Delay (days)'
    )
