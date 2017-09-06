# -*- coding: utf-8 -*-
# Copyright 2016 Eficent Business and IT Consulting Services S.L.
#   (http://www.eficent.com)
# © 2016 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    'name': 'Account Check Printing Report DLT103',
    'version': '10.0.1.0.0',
    'license': 'AGPL-3',
    'author': "Eficent,"
              "Serpent Consulting Services Pvt. Ltd.,"
              "Odoo Community Association (OCA)",
    'category': 'Generic Modules/Accounting',
    'website': "https://github.com/OCA/account-payment",
    'depends': ['account_check_printing_report_base'],
    'data': [
        'data/report_paperformat.xml',
        'data/report_paperformat_parameter.xml',
        'data/account_payment_check_report_data.xml',
        'views/report_check.xml',
        'report/account_check_writing_report.xml',
    ],
    'installable': True,
}
