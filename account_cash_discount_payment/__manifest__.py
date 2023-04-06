# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account Cash Discount Payment",
    "version": "14.0.1.0.2",
    "author": "ACSONE SA/NV," "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-payment",
    "license": "AGPL-3",
    "category": "Accounting",
    "depends": ["account_cash_discount_base", "account_payment_order_grouped_output"],
    "data": [
        "views/account_move_line.xml",
        "views/account_payment_line.xml",
        "wizards/account_payment_line_create.xml",
    ],
}
