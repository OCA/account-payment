# Copyright (C) 2017-2021 Creu Blanca
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

{
    "name": "Account cash invoice",
    "version": "14.0.1.2.0",
    "category": "Accounting",
    "author": "Creu Blanca,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-payment",
    "summary": "Pay and receive invoices from bank statements",
    "license": "LGPL-3",
    "depends": ["account"],
    "data": [
        "security/ir.model.access.csv",
        "wizard/cash_invoice_out.xml",
        "wizard/cash_invoice_in.xml",
    ],
}
