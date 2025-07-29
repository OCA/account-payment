# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account Payment Return Revoke Mandate",
    "summary": """
        This addon adds an option on return codes
        in order to cancel mandates associated.""",
    "version": "12.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-payment",
    "depends": ["account_banking_mandate", "account_payment_return"],
    "data": ["views/payment_return_reason.xml"],
    "demo": [],
}
