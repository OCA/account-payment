# -*- coding: utf-8 -*-
# Copyright 2017 Ursa Information Systems <http://www.ursainfosystems.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Credit Card Payments",
    "summary": "Add support for credit card payments",
    "version": "10.0.1.0.0",
    "license": "AGPL-3",
    "author": "Ursa Information Systems, Odoo Community Association (OCA)",
    "category": "Accounting & Finance",
    "maintainer": "Ursa Information Systems",
    "website": "http://www.ursainfosystems.com",
    "depends": [
        "account_accountant",
        "account_voucher",
    ],
    "data": [
        "views/account_view.xml",
    ],
    "installable": True,
}
