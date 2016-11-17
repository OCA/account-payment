# -*- coding: utf-8 -*-
# Copyright 2016 Serpent Consulting Services Pvt. Ltd
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Payment Order Under Payment",
    "summary": "Payment Order Under Payment",
    "version": "8.0.1.0.0",
    "category": "Accounting",
    'website': 'http://www.serpentcs.com',
    "author": """Serpent Consulting Services Pvt. Ltd.,
                Agile Business Group,
                Odoo Community Association (OCA)""",
    "license": "AGPL-3",
    "depends": [
        "account_payment",
        "account_banking_payment_export"
    ],
    "data": [
        "views/payment_line_views.xml",
        "views/move_line_views.xml",
        "views/invoice_view.xml",
    ],
    "installable": True,
}
