# Copyright 2013-2016 Camptocamp SA (Yannick Vaucher)
# Copyright 2015-2016 Akretion
# (Alexis de Lattre <alexis.delattre@akretion.com>)
# Copyright 2020 Tecnativa - Víctor Martínez
# Copyright 2021 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Payment Term Extension",
    "version": "13.0.3.0.3",
    "category": "Accounting & Finance",
    "summary": "Adds rounding, months, weeks and multiple payment days "
    "properties on payment term lines",
    "author": "Camptocamp,"
    "Tecnativa,"
    "Agile Business Group, "
    "Odoo Community Association (OCA)",
    "maintainer": "OCA",
    "website": "https://github.com/OCA/account-payment/",
    "license": "AGPL-3",
    "depends": ["account"],
    "data": ["security/ir.model.access.csv", "views/account_payment_term.xml"],
    "demo": ["demo/account_demo.xml"],
    "installable": True,
}
