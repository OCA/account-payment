# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Payment due list with payment mode",
    "version": "11.0.1.0.0",
    "category": "Generic Modules/Payment",
    'author': 'Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/account-payment',
    'license': 'LGPL-3',
    "depends": [
        "account_payment_partner",
        "account_due_list",
    ],
    "data": [
        'views/payment_view.xml',
    ],
    'installable': True,
    "auto_install": False,
}
