# -*- coding: utf-8 -*-
# Copyright 2016 Eficent Business and IT Consulting Services S.L.
#   (http://www.eficent.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    'name': 'Account Check Report',
    'version': '10.0.1.0.0',
    'license': 'AGPL-3',
    'author': "Eficent,"
              "Odoo Community Association (OCA)",
    'category': 'Generic Modules/Accounting',
    'website': "https://github.com/OCA/account-payment",
    'depends': ["account"],
    'data': [
        'report/account_check_report.xml',
    ],
    'installable': True,
}
