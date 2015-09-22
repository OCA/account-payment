# -*- encoding: utf-8 -*-
##############################################################################
#
#    Module Writen to OpenERP, Open Source Management Solution
#    Copyright (C) 2015 OBERTIX FREE SOLUTIONS (<http://obertix.net>).
#                       cubells <vicent@vcubells.net>
#
#    All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
##############################################################################

{
    "name": "Payment due list with payment mode",
    "version": "8.0.1.0.0",
    "category": "Generic Modules/Payment",
    "author": "Odoo Community Association (OCA),"
              "Obertix, Free Solutions",
    "contributors": ["cubells <vicent@vcubells.net>"],
    "website": "http://www.obertix.net",
    "depends": [
        "account_payment_partner",
        "account_due_list",
    ],
    "data": [
        'views/payment_view.xml',
    ],
    "installable": True,
    "auto_install": True,
}
