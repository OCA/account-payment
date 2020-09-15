# Copyright (C) 2020 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Multiple Payments: force memo field available',
    'summary': 'Adds Memo on Batch Payments',
    'version': '12.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'Open Source Integrators, Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/account-payment',
    'category': 'Accounting & Finance',
    'depends': [
        'account',
    ],
    'data': [
        'wizard/account_register_payments_view.xml',
    ],
    'installable': True,
}
