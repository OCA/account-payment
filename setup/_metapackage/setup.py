import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-account-payment",
    description="Meta package for oca-account-payment Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-account_due_list>=16.0dev,<16.1dev',
        'odoo-addon-account_due_list_aging_comment>=16.0dev,<16.1dev',
        'odoo-addon-account_due_list_payment_mode>=16.0dev,<16.1dev',
        'odoo-addon-account_payment_multi_deduction>=16.0dev,<16.1dev',
        'odoo-addon-account_payment_notification>=16.0dev,<16.1dev',
        'odoo-addon-account_payment_promissory_note>=16.0dev,<16.1dev',
        'odoo-addon-account_payment_return>=16.0dev,<16.1dev',
        'odoo-addon-account_payment_return_import>=16.0dev,<16.1dev',
        'odoo-addon-account_payment_return_import_iso20022>=16.0dev,<16.1dev',
        'odoo-addon-account_payment_term_extension>=16.0dev,<16.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 16.0',
    ]
)
