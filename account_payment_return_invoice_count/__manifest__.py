# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account Payment Return Invoice Count",
    "summary": """
        This addon allows to count return payments
        on invoices and block them eventually.""",
    "version": "12.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-payment",
    "depends": ["account_payment_return"],
    "data": ["views/res_config_settings.xml", "views/account_invoice.xml"],
    "demo": [],
    "post_init_hook": "post_init_hook",
}
