# Copyright 2016 Cyril Gaudin (Camptocamp)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    'name': 'Account Early Payment Discount',
    'version': '12.0.1.0.1',
    'author': 'Camptocamp, Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'category': 'Accounting & Finance',
    'website': 'https://github.com/OCA/account-payment',
    'depends': [
        'account',
    ],
    'data': [
        'views/account_payment_term.xml',
    ],
    'installable': True,
    'auto_install': False,
}
