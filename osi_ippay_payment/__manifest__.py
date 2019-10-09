# Copyright (C) 2019 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "OSI Prismpay Payment",
    "version": "12.0.1.0.0",
    "license": "AGPL-3",
    "description": "Prismpay Payment",
    "author": "Open Source Integrators",
    "maintainer": "Open Source Integrators",
    "website": "http://www.opensourceintegrators.com",
    "category": "Accounting",
    "images": [],
    "depends": ['osi_add_credit_card'],
    "data": [
        "data/prismpay_payment_data.xml",
        "views/payment_view.xml",
    ],
    "auto_install": False,
    "application": False,
    "installable": True,
}
