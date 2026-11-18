# Copyright 2022 ForgeFlow, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

{
    "name": "Payment Counterpart Lines",
    "summary": """Payment Counterpart Lines""",
    "author": "ForgeFlow S.L., Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-payment",
    "category": "Account",
    "version": "18.0.1.0.2",
    "license": "AGPL-3",
    "depends": ["account_payment"],
    "data": [
        "security/ir.model.access.csv",
        "views/res_config_settings_views.xml",
        "views/account_payment_views.xml",
    ],
    "maintainers": ["ChrisOForgeFlow"],
    "installable": True,
    "auto_install": False,
}
