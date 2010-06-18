# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-2010 Pexego Sistemas Informáticos. All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
"""
Account Journal extensions for the cash statements.
"""
__authors__ = [
    "Luis Manuel Angueira Blanco (Pexego) <manuel@pexego.es",
    "Borja López Soilán (Pexego) <borjals@pexego.es>"
]

from osv import osv, fields

class account_journal(osv.osv):
    """
    Extend the account journal to add the show_in_cash_statements field.
    """
    _inherit = 'account.journal'

    _columns = {
        'show_in_cash_statements': fields.boolean('Show in Cash Statements', help="If enabled, this journal will be available on the Entries by Cash Statements."),
    }

    _defaults = {
        'show_in_cash_statements': lambda *a : False,
    }

account_journal()
