# Copyright 2016 Carlos Dauden <carlos.dauden@tecnativa.com>
# Copyright 2016-2020 Tecnativa - Pedro M. Baeza
# Copyright 2017 David Vidal <david.vidal@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account Payment Return Import",
    "category": "Accounting",
    "version": "13.0.1.0.3",
    "summary": "This module adds a generic wizard to import payment return"
    "file formats. Is only the base to be extended by another"
    "modules",
    "license": "AGPL-3",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-payment",
    "depends": ["account_payment_return"],
    "data": ["views/payment_return_view.xml", "wizard/payment_return_import_view.xml"],
    "installable": True,
}
