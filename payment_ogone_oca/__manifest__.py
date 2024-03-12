# Copyright 2022 Odoo SA
# Copyright 2023 Chafique Delli <chafique.delli@akretion.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Payment Provider: Ogone",
    "category": "Accounting/Payment Providers",
    "version": "16.0.1.0.0",
    "license": "LGPL-3",
    "summary": "Payment Provider: Ogone Implementation",
    "author": "Odoo SA, Akretion, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-payment",
    "depends": ["account_payment"],
    "data": [
        "views/payment_ogone_templates.xml",
        "views/payment_provider_views.xml",
        "data/payment_provider_data.xml",
    ],
    "post_init_hook": "post_init_hook",
    "uninstall_hook": "uninstall_hook",
    "installable": True,
}
