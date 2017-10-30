# -*- coding: utf-8 -*-
# Copyright 2017 Mhadhbi Achraf(https://github.com/AMhadhbi).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    'name': 'Account Payment Confirm',
    'version': '10.0.1.0.0',
    'category': 'Finance',
    'summary': "Confirm payments in draft state",
    'author': "Mhadhbi Achraf,Odoo Community Association (OCA)",
    'website': 'https://github.com/AMhadhbi',
    'license': 'AGPL-3',
    'depends': ['account'],
    'data': [
        'wizard/payment_confirm_view.xml',
    ],
    'installable': True,
}
