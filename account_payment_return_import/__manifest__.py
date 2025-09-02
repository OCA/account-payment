# Copyright 2016 Tecnativa - Carlos Dauden
# Copyright 2016-2020 Tecnativa - Pedro M. Baeza
# Copyright 2017 Tecnativa - David Vidal
# Copyright 2024 Tecnativa - Carolina Fernandez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account Payment Return Import",
    "category": "Accounting",
    "version": "18.0.1.0.1",
    "development_status": "Mature",
    "summary": "This module adds a generic wizard to import payment return"
    "file formats. Is only the base to be extended by another"
    "modules",
    "license": "AGPL-3",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-payment",
    "depends": ["account_payment_return"],
    "data": [
        "security/ir.model.access.csv",
        "views/payment_return_view.xml",
        "wizard/payment_return_import_view.xml",
    ],
    "installable": True,
}
