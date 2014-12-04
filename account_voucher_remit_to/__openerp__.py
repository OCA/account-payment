# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Eficent (<http://www.eficent.com/>)
#              Jordi Ballester Alomar <jordi.ballester@eficent.com>
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
    "name": "Account Voucher Remit-to address",
    "version": "1.0",
    "author": "Eficent",
    "website": "www.eficent.com",
    "category": "Accounting",
    "depends": ["account_voucher", "partner_relations"],
    "description": """
Introduction
------------
This module aims to introduce the possibility to assign a remit-to address
to a partner, that is then used at the time of printing a voucher.

It uses the module 'Partner relations' available in the OCA project "partner-contact".

    """,
    "init_xml": [],
    "update_xml": [    
        "data/partner_relation_data.xml",
        "data/company_data.xml",
        "res_company_view.xml",
        "account_voucher_view.xml",
        "voucher_payment_receipt_view.xml",
        "voucher_sales_purchase_view.xml",
    ],
    'demo_xml': [

    ],
    'test':[
    ],
    'installable': True,
    'active': False,
    'certificate': '',
}