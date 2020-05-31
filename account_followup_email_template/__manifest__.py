# -*- coding: utf-8 -*-
# License LGPL-3 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': 'Account follow up email template',
    'version': '1.0',
    'category': 'Accounting & Finance',
    'summary': '''
        This module add email template for payment follow up.
    ''',
    'author': 'TRESCLOUD, Odoo Community Association (OCA)',
    'website': 'http://www.trescloud.com',
    'images': ['static/description/icon.png'],
    'license': 'LGPL-3',
    'depends': [
        'base',
        'account'
    ],
    'data': [
        'data/followup_template_data.xml'
    ],
    'installable': True
}