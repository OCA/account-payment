# Copyright 2022 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
{
    "name": "Account payment notification",
    "summary": "Notifiy upcoming payments",
    "version": "10.0.1.0.1",
    "development_status": "Beta",
    "category": "Accounting",
    "website": "https://github.com/OCA/account-payment",
    "author": "Moduon, Odoo Community Association (OCA)",
    "maintainers": ["yajo"],
    "license": "LGPL-3",
    "installable": True,
    "depends": [
        "account",
        "mail",
        "account_check_report",
    ],
    "data": [
        "data/mail_template.xml",
        "views/account_payment_views.xml",
        "wizards/res_config_settings_views.xml",
    ],
}
