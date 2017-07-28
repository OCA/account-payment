# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Business Applications
#    Copyright (C) 2016 Savoir-faire Linux
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import fields, models


class AccountConfigSettings(models.TransientModel):
    _inherit = 'account.config.settings'

    disable_voucher_auto_lines = fields.Boolean(
        'No auto lines on voucher',
        related="company_id.disable_voucher_auto_lines",
        help="Check this box to disable automatic matching of lines "
        "on the account voucher."
    )
