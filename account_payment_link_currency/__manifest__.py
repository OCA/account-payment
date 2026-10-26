# Copyright 2026 volkantasci
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

{
    "name": "Account Payment Link Currency",
    "summary": "Select currency and auto-convert amounts in invoice payment links",
    "version": "19.0.1.0.0",
    "development_status": "Beta",
    "category": "Accounting/Payment",
    "website": "https://github.com/OCA/account-payment",
    "author": "volkantasci, Odoo Community Association (OCA)",
    "maintainers": ["volkantasci"],
    "license": "LGPL-3",
    "application": False,
    "installable": True,
    "auto_install": False,
    "depends": [
        "account_payment",
        "payment",
    ],
    "data": [
        "views/payment_link_wizard_views.xml",
    ],
}
