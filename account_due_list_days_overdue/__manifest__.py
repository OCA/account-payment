# Copyright 2016 ForgeFlow S.L.
#   (<http://www.forgeflow.com>).
# Copyright 2016 Therp BV (<http://therp.nl>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Payments Due list days overdue",
    "version": "13.0.1.0.2",
    "category": "Accounting",
    "author": "Odoo Community Association (OCA), ForgeFlow",
    "website": "https://github.com/OCA/account-payment",
    "license": "AGPL-3",
    "depends": ["account_due_list"],
    "data": [
        "security/ir.model.access.csv",
        "views/account_overdue_term_view.xml",
        "views/account_move_line_view.xml",
    ],
    "demo": ["demo/account_overdue_term_demo.xml"],
    "installable": True,
}
