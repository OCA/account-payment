# encoding: utf-8
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2012 Zikzakmedia S.L. (http://zikzakmedia.com)
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
    "name" : "Purchase early payment discount",
    "version" : "1.0",
    "author" : "Zikzakmedia SL, Pexego, Odoo Community Association (OCA)",
    "depends" : [
        "sale_early_payment_discount",
    ],
    "license": "AGPL-3",
    "category" : "Payment",
    "data" : [
        'partner_payment_term_early_discount_view.xml',
        'purchase_view.xml',
        'account_invoice_view.xml',
        'product_category_view.xml',
    ],
    'installable': True,
}
