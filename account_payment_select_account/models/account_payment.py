# Copyright (C) 2016-Today: La Louve (<http://www.cooplalouve.fr/>)
# Copyright (C) 2019-Today: Druidoo (<https://www.druidoo.io>)
# @author: La Louve
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html

from odoo import fields, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    outstanding_account_id = fields.Many2one(readonly=False)
