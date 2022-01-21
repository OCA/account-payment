# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account Cash Discount Write Off",
    "summary": """
        Create an automatic writeoff for payment with discount on the payment
        order confirmation""",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-payment",
    "depends": ["account_cash_discount_payment"],
    "data": ["views/res_company.xml"],
    "demo": [],
}
