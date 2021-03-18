# Copyright 2011-2012 7 i TRIA <http://www.7itria.cat>
# Copyright 2011-2012 Avanzosc <http://www.avanzosc.com>
# Copyright 2013 Tecnativa - Pedro M. Baeza
# Copyright 2014 Markus Schneider <markus.schneider@initos.com>
# Copyright 2015 Tecnativa - Sergio Teruel
# Copyright 2015-2017 Tecnativa - Pedro M. Baeza
# Copyright 2016 Tecnativa - Carlos Dauden
# Copyright 2017 Tecnativa - David Vidal
# Copyright 2021 Tecnativa - João Marques
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account Payment Returns",
    "version": "14.0.1.0.0",
    "summary": "Manage the return of your payments",
    "license": "AGPL-3",
    "depends": ["mail", "account"],
    "author": "Odoo Community Association (OCA),"
    "7 i TRIA, "
    "Tecnativa, "
    "initOS GmbH & Co., ",
    "website": "https://github.com/OCA/account-payment",
    "data": [
        "security/ir.model.access.csv",
        "security/account_payment_return_security.xml",
        "views/assets.xml",
        "views/payment_return_view.xml",
        "views/account_journal_view.xml",
        "data/ir_sequence_data.xml",
        "views/account_move_views.xml",
    ],
    "qweb": ["static/src/xml/account_payment_return.xml"],
    "installable": True,
}
