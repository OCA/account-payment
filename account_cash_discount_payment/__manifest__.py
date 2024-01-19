# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account Cash Discount Payment",
    "version": "16.0.1.0.1",
    "author": "ACSONE SA/NV," "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-payment",
    "license": "AGPL-3",
    "category": "Accounting",
    "depends": [
        "account",
        "account_payment_order",
    ],  # account_payment_order_grouped_output
    "data": [
        "views/account_payment_line.xml",
        "wizards/account_payment_line_create.xml",
    ],
}
