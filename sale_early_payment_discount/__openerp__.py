# encoding: utf-8
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
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
    'name' : 'Sale early payment discount',
    'version' : '1.0',
    'license': 'AGPL-3',
    'author' : 'Pexego, Odoo Community Association (OCA)',
    'depends' : ['base', 'product', 'account', 'sale', 'sale_stock', 'stock',
                 'stock_account', 'decimal_precision'],
    'category' : 'Enterprise Specific Modules',
    'data' : ['security/ir.model.access.csv',
                    'data/product_product.xml',
                    'partner_payment_term_early_discount_view.xml',
                    'partner_view.xml',
                    'payment_term_view.xml',
                    'sale_view.xml',
                    'account_invoice_view.xml',
                    'product_category_view.xml',
                    'report/sale_order.xml'],
    'installable': True
}
