# -*- coding: utf-8 -*-
# © 2016 Cyril Gaudin (Camptocamp)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Account Early Payment Discount',
    'version': '9.0.1.0.0',
    'author': 'Camptocamp, Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'category': 'Accountnig & Finance',
    'website': 'http://www.camptocamp.com',
    'depends': [
        'account',
    ],
    'data': [
        'views/account_payment_term.xml',
    ],
    'installable': True,
    'auto_install': False,
}
