# -*- coding: utf-8 -*-
# © 2013 Agile Business Group sagl
# © 2016 Savoir-faire Linux
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


{
    'name': "Source Document in Customer Payments",
    'version': '8.0.1.0.0',
    'category': 'Accounting & Finance',
    'author': (
        'Agile Business Group sagl,'
        'Savoir-faire linux,'
        'Odoo Community Association'
    ),
    'website': 'http://www.agilebg.com',
    'license': 'AGPL-3',
    "depends": ['account_voucher'],
    "data": [
        'views/account_voucher.xml',
    ],
    "active": False,
    "installable": True
}
