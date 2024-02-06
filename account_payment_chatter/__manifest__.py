# -*- coding: utf-8 -*-
# Copyright 2023 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Chatter on account payments',
    'version': '10.0.1.0.0',
    'category': 'Invoices & Payments',
    'license': 'AGPL-3',
    'author': 'ForgeFlow, '
              'Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/account-payment',
    'depends': [
        'account',
    ],
    'data': [
        'views/account_payment_views.xml',
    ],
    'installable': True,
    'development_status': 'Alpha',
    'maintainers': ['AaronHForgeFlow'],
}
