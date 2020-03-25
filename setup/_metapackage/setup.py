import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo13-addons-oca-account-payment",
    description="Meta package for oca-account-payment Odoo addons",
    version=version,
    install_requires=[
        'odoo13-addon-account_due_list',
        'odoo13-addon-account_due_list_payment_mode',
        'odoo13-addon-account_payment_multi_deduction',
        'odoo13-addon-account_payment_return',
        'odoo13-addon-partner_aging',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
