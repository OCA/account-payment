# -*- coding: utf-8 -*-
# © 2013 Agile Business Group sagl
# © 2016 Savoir-faire Linux
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': "Supplier Invoice Number In Payment Vouchers",
    'version': '8.0.2.0.0',
    'category': 'Accounting & Finance',
    'author': (
        "Agile Business Group,"
        "Savoir-faire Linux,"
        "Odoo Community Association (OCA),"
        u"Blanco Martín & Asociados"
    ),
    'website': 'http://www.agilebg.com',
    'license': 'AGPL-3',
    "depends": ['account_voucher'],
    "data": [
        'views/account_voucher.xml',
    ],
    "installable": True,
}