# Copyright 2023 ForgeFlow, S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

{
    "name": "Payment Counterpart Lines Import XLSX",
    "summary": """Payment Counterpart Lines Import XLSX""",
    "author": "ForgeFlow S.L., Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-payment",
    "category": "Account",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["account_payment_line", "excel_import_export"],
    "data": [
        "views/account_payment_view.xml",
        "data/import_template.xml",
    ],
    "maintainers": ["ChrisOForgeFlow"],
    "installable": True,
    "auto_install": False,
}
