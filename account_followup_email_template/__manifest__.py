# -*- coding: utf-8 -*-
# License LGPL-3 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': 'Account follow up email template',
    'version': '1.0',
    'category': 'Accounting & Finance',
    'summary': '''
        This module add email template for payment follow up.
    ''',
    'author': 'TRESCLOUD CIA LTDA',
    'maintainer': 'TRESCLOUD CIA. LTDA.',
    'website': 'http://www.trescloud.com',
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