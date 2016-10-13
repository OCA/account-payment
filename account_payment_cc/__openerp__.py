# -*- coding: utf-8 -*-
#  account_payment_cc - CREDIT CARD PAYMENTS for OpenERP
#  Copyright (C) 2012 - TODAY, Ursa Information Systems (<http://ursainfosystems.com>)
#  Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>)
#  contact@ursainfosystems.com


{
    'name' : 'Credit Card Payments',
    'version' : '8.0.1.8.0',
    'author' : 'Ursa Information System, OpenERP SA, Odoo Community Association (OCA)',
    'summary': 'Adds support for Credit Card AP movements',
    'maintainer': 'Ursa Information Systems',
    'website': 'http://www.ursainfosystems.com',
    'category': 'Accounting & Finance',
    'depends' : ['account_voucher'],
    'data' : ['views/account_view.xml',
    ],
    'auto_install': False,
    'application': False,
    'installable': True,
}
