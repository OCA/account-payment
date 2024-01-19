# Copyright 2024 Grupo Isonor
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account Payment Sign",
    "version": "15.0.1.0.0",
    "author": "Grupo Isonor, Odoo Community Association (OCA)",
    "category": "Accounting/Accounting",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/account-payment",
    "depends": [
        "account_payment",
    ],
    "data": [
        "views/res_config_settings_views.xml",
        "views/account_portal_templates.xml",
        "views/account_move_views.xml",
        "report/invoice_report_templates.xml",
    ],
    "installable": True,
}
