# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today: La Louve (<http://www.lalouve.net/>)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Account Payment - Transfer Account',
    'version': '9.0.1.0.0',
    'category': 'Accounting & Finance',
    'author': 'La Louve, Odoo Community Association (OCA)',
    'website': 'http://www.lalouve.net',
    'depends': [
        'account',
        'account_cancel',
        'l10n_generic_coa',
    ],
    'data': [
        'views/view_account_payment.xml',
        'views/view_account_account.xml',
    ],
    'demo': [
        'demo/account_account.xml',
    ],
    'installable': True,
}
