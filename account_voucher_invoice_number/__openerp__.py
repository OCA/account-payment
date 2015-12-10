# -*- coding: utf-8 -*-
# © 2015 Lorenzo Battistini - Agile Business Group
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Voucher invoices Number",
    "summary": "Display linked invoices in voucher list",
    "version": "8.0.1.0.0",
    "category": "Accounting & Finance",
    "website": "http://www.agilebg.com/",
    "author": "Agile Business Group, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "account_voucher",
    ],
    "data": [
        'views/account_voucher_view.xml',
    ],
    "images": [
        'images/vouchers.png',
    ],
}
