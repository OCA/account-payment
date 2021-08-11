# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account Payment Term Partner Holiday",
    "version": "12.0.2.0.0",
    "website": "https://github.com/OCA/account-payment",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": ["account_payment_term_extension"],
    "maintainers": ["victoralmau"],
    "development_status": "Production/Stable",
    "data": [
        "security/ir.model.access.csv",
        "views/res_partner_view.xml"
    ],
}
