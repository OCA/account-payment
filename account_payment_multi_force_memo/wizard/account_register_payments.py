# Copyright (C) 2020 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountRegisterPayments(models.TransientModel):
    _inherit = 'account.register.payments'

    show_communication_field = fields.Boolean(string='Show Memo')
