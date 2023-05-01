import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo13-addons-oca-account-payment",
    description="Meta package for oca-account-payment Odoo addons",
    version=version,
    install_requires=[
        'odoo13-addon-account_cash_discount_base',
        'odoo13-addon-account_cash_discount_base_sale',
        'odoo13-addon-account_cash_discount_payment',
        'odoo13-addon-account_cash_discount_write_off',
        'odoo13-addon-account_cash_invoice',
        'odoo13-addon-account_check_date',
        'odoo13-addon-account_check_printing_report_base',
        'odoo13-addon-account_due_list',
        'odoo13-addon-account_due_list_days_overdue',
        'odoo13-addon-account_due_list_payment_mode',
        'odoo13-addon-account_payment_multi_deduction',
        'odoo13-addon-account_payment_promissory_note',
        'odoo13-addon-account_payment_return',
        'odoo13-addon-account_payment_return_import',
        'odoo13-addon-account_payment_return_import_iso20022',
        'odoo13-addon-account_payment_show_invoice',
        'odoo13-addon-account_payment_term_extension',
        'odoo13-addon-account_payment_term_partner_holiday',
        'odoo13-addon-account_payment_term_security',
        'odoo13-addon-partner_aging',
        'odoo13-addon-sale_payment_mgmt',
        'odoo13-addon-sale_payment_term_security',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 13.0',
    ]
)
