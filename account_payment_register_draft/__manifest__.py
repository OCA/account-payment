# Copyright 2024 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Account Payment Register - Draft",
    "version": "15.0.1.0.0",
    "summary": "Allow register payment to draft state",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-payment",
    "license": "AGPL-3",
    "category": "Accounting",
    "depends": ["account"],
    "data": [
        "views/res_config_settings_views.xml",
        "views/account_move_views.xml",
        "views/account_payment_view.xml",
    ],
    "installable": True,
    "development_status": "Alpha",
    "maintainers": ["Saran440"],
}
