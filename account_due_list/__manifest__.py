# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Payments Due list",
    "version": "16.0.1.0.2",
    "category": "Generic Modules/Payment",
    "development_status": "Production/Stable",
    "author": "Odoo Community Association (OCA)",
    "summary": "List of open credits and debits, with due date",
    "website": "https://github.com/OCA/account-payment",
    "license": "AGPL-3",
    "depends": ["account"],
    "data": ["views/payment_view.xml"],
    "pre_init_hook": "pre_init_hook",
    "installable": True,
    "auto_install": False,
}
