# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011-2012 Domsense s.r.l. (<http://www.domsense.com>).
#    Copyright (C) 2012-2014 Agile Business Group sagl
#    (<http://www.agilebg.com>)
#    @author Lorenzo Battistini <lorenzo.battistini@agilebg.com>
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
{
    "name": "Cash basis extensions for vouchers",
    "version": "8.0.1.0.0",
    'category': 'Hidden/Dependency',
    "depends": ["account_voucher"],
    "author": "Agile Business Group",
    "website": "http://www.agilebg.com",
    "license": "AGPL-3",
    "description": """
In some countries, under certain conditions, companies can apply the cash
basis.
The cash basis means businesses may account for VAT as payment comes in from
their customers.
It is easier to manage than the normal method, which forces businesses to
account for VAT based on invoices issued, regardless of whether or not the
money has come in.
The key advantage to accounting for VAT on a cash basis is the cashflow benefit
to your business.
The effect of the cash basis is that you only become liable for VAT when you
have actually received payment, so you don't have to fund the VAT on your
debtors.
This is particularly helpful in a startup situation and in the case of an
expanding business.

This module gathers all the basic functionalities that allow to handle the
cash basis.
    """,
    'data': [
        'company_view.xml',
        'voucher_view.xml',
    ],
    'demo': [],
    'installable': True,
}
