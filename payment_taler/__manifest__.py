# SPDX-FileCopyrightText: 2025 Mael Panouillot <panouillot.mael@gmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

{
    'name': 'Taler-Odoo Payment System',
    'version': '18.0.1.0',
    'summary': 'Integration of the Taler payment system in Odoo.',
    'author': 'Nemael',
    'category': 'Accounting/Payment Providers',
    'website': 'https://codeberg.org/Nemael/tops',
    'images': ['images/thumbnail.png'],
    'depends': ['payment', 'website', 'website_sale', 'account', 'point_of_sale'],
    'data': [
        'views/taler_payment_template.xml',
        'views/taler_provider_view.xml',
        'views/taler_invoice_view.xml',
        'data/taler_payment_method_data.xml',
        'data/taler_payment_provider_data.xml',
        'data/email_refund_template_data.xml',
        'security/ir.model.access.csv' #The ir security file is not actually used for now, but it will stay included in the files.
    ],
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'installable': True,
    'application': True,
    'license': 'LGPL-3' #Complete license is "LGPL-3.0-or-later", see on top of any files in the module.
}
