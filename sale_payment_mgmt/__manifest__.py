# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Sale Payment Management",
    "version": "13.0.1.0.0",
    "category": "Sales/Sales",
    "development_status": "Production/Stable",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "summary": "List and create customer payments for salesmen",
    "website": "https://github.com/OCA/account-payment",
    "license": "AGPL-3",
    "depends": ["payment", "sale_management", "sales_team"],
    "conflicts": ["account_payment_multi_deduction"],
    "maintainers": ["victoralmau"],
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "views/account_move_view.xml",
        "views/account_payment_view.xml",
    ],
    "installable": True,
    "auto_install": False,
}
