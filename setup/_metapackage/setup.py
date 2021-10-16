import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo9-addons-oca-account-payment",
    description="Meta package for oca-account-payment Odoo addons",
    version=version,
    install_requires=[
        'odoo9-addon-account_check_printing_report_base',
        'odoo9-addon-account_check_printing_report_dlt103',
        'odoo9-addon-account_due_list',
        'odoo9-addon-account_due_list_aging_comments',
        'odoo9-addon-account_due_list_days_overdue',
        'odoo9-addon-account_due_list_payment_mode',
        'odoo9-addon-account_partner_reconcile',
        'odoo9-addon-account_payment_return',
        'odoo9-addon-account_payment_return_import',
        'odoo9-addon-account_payment_return_import_sepa_pain',
        'odoo9-addon-account_payment_show_invoice',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 9.0',
    ]
)
