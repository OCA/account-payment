# Copyright 2019 Tecnativa <vicent.cubells@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    'name': 'Account Receipt Report',
    'version': '11.0.1.0.0',
    'category': 'Accounting',
    'author': 'Odoo Community Association (OCA),'
              'Tecnativa',
    'summary': 'Add option to print account payment receipt',
    'website': 'https://github.com/OCA/account-payment',
    'license': 'AGPL-3',
    'depends': [
        'account',
    ],
    'data': [
        'reports/payment_receipt_report.xml',
        'views/account_payment_views.xml',
        'views/account_views.xml',
    ],
    'installable': True,
}
