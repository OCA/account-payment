import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo8-addons-oca-account-payment",
    description="Meta package for oca-account-payment Odoo addons",
    version=version,
    install_requires=[
        'odoo8-addon-account_due_list',
        'odoo8-addon-account_due_list_aging_comments',
        'odoo8-addon-account_due_list_days_overdue',
        'odoo8-addon-account_due_list_payment_mode',
        'odoo8-addon-account_payment_extension',
        'odoo8-addon-account_payment_order_sequence',
        'odoo8-addon-account_payment_order_to_voucher',
        'odoo8-addon-account_payment_return',
        'odoo8-addon-account_payment_return_import',
        'odoo8-addon-account_payment_return_import_sepa_pain',
        'odoo8-addon-account_payment_term_multi_day',
        'odoo8-addon-account_vat_on_payment',
        'odoo8-addon-account_voucher_cash_basis',
        'odoo8-addon-account_voucher_invoice_number',
        'odoo8-addon-account_voucher_source_document',
        'odoo8-addon-account_voucher_supplier_invoice_number',
        'odoo8-addon-purchase_payment',
        'odoo8-addon-sale_payment',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
