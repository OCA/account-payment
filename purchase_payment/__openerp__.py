# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2010 Pexego S.L. (http://www.pexego.es) All Rights Reserved.
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
{
    "name" : "Purchase Payment Type and Terms",
    "version" : "1.0",
    "author" : "Pexego,Odoo Community Association (OCA)",
    "website": "www.pexego.es",
    "license": "GPL-3 or any later version",
    "category" : 'Generic Modules/Sales & Purchases',
    "description": """Adds payment info to the purchase process.

Adds payment type, terms, and bank account to the purchase orders.

Allows to set different default payment terms for purchases (the partners
will have payment terms and supplier payment terms).

The payment terms, payment type and bank account default values for the
purchase will be taken from the partner.

Invoices created from purchase orders, or from pickings related to purchase
orders, will inherit this payment info from the payment order.
""",
    "depends" : [
            "account_payment",
            "account_payment_extension",
            "purchase",
            "stock",
        ],
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : [
            "purchase_payment_view.xml",
        ],
    "active": False,
    "installable": False,
}
