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
    "author": "Eficent, Odoo Community Association (OCA)",
    "website": "www.eficent.com",
    "category": "Accounting",
    "depends": ["account_voucher"],
    "description": """
Account Voucher Remit-to address
================================
This module aims to introduce the possibility to assign a remit-to address
to a partner, that is then used at the time of printing a voucher.

The remit-to address is typically used related to the preparation of checks.


Installation
============

No additional installation instructions are required.


Configuration
=============

This module does not require any additional configuration.

Usage
=====

The user can create a partner with address type 'Remit-to'.

When the user creates a voucher for a partner, if this partner has a related
partner with address type 'Remit-to', it will be proposed.


Known issues / Roadmap
======================

The address type field is redefined in this module to add the new type
'remit-to'. Extension of selection fields is a problem in v7, because any
other module that also extends this field will cause the extended address
type to disappear.


Credits
=======

Contributors
------------

* Jordi Ballester <jordi.ballester@eficent.com>

Maintainer
----------

.. image:: http://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: http://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit http://odoo-community.org.
    """,
    "data": [
        "views/account_voucher_view.xml",
        "views/voucher_payment_receipt_view.xml",
        "views/voucher_sales_purchase_view.xml",
    ],
    'demo': [
    ],
    'test':[
    ],
    'installable': True,
    'active': False,
    'certificate': '',
}