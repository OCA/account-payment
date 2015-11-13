# -*- coding: utf-8 -*-
# © 2015 Eficent
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Account voucher remit-to address",
    "summary": "Account voucher remit-to address",
    "version": "7.0.1.0.0",
    "category": "Accounting",
    "website": "https://odoo-community.org/",
    "author": "Eficent, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "external_dependencies": {
        "python": [],
        "bin": [],
    },
    "depends": [
        "account_voucher"
    ],
    "data": [
        "views/account_voucher_view.xml",
        "views/voucher_payment_receipt_view.xml",
        "views/voucher_sales_purchase_view.xml",
    ]
}