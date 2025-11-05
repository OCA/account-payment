# Copyright 2025 Juan Carlos Oñate - Tecnativa <juancarlos.onate@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "SeQura Payment Provider",
    "summary": "Integrates SeQura as a payment provider",
    "version": "18.0.1.0.0",
    "category": "Accounting/Payment Providers",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "maintainers": ["juancarlosonate-tecnativa"],
    "license": "AGPL-3",
    "website": "https://github.com/OCA/account-payment",
    "depends": ["sale", "stock"],
    "data": [
        "views/payment_provider_views.xml",
        "views/payment_sequra_templates.xml",
        "data/payment_provider_data.xml",
        "data/stock_picking_actions.xml",
    ],
    "post_init_hook": "post_init_hook",
    "uninstall_hook": "uninstall_hook",
    "installable": True,
}
