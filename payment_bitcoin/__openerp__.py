# -*- coding: utf-8 -*-
# © initOS GmbH 2016
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Bitcoin Payment Acquirer',
    'category': 'Hidden',
    'summary': 'Payment Acquirer: Bitcoin Transfer Implementation',
    'version': '8.0.1.0.0',
    'description': """Bitcoin Transfer Payment Acquirer""",
    'author': 'initOS GmbH, Odoo Community Association (OCA)',
    'depends': [
        'payment',
        'sale',
        'website'
    ],
    'data': [
        'views/bitcoin.xml',
        'views/transfer.xml',
        'views/templates.xml',
        'data/transfer.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': False,
}
