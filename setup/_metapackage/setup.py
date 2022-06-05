import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo14-addons-oca-account-payment",
    description="Meta package for oca-account-payment Odoo addons",
    version=version,
    install_requires=[
        'odoo14-addon-account_cash_discount_base',
        'odoo14-addon-account_cash_discount_payment',
        'odoo14-addon-account_cash_discount_write_off',
        'odoo14-addon-account_cash_invoice',
        'odoo14-addon-account_due_list',
        'odoo14-addon-account_due_list_aging_comment',
        'odoo14-addon-account_due_list_days_overdue',
        'odoo14-addon-account_due_list_payment_mode',
        'odoo14-addon-account_payment_batch_process',
        'odoo14-addon-account_payment_batch_process_discount',
        'odoo14-addon-account_payment_credit_card',
        'odoo14-addon-account_payment_multi_deduction',
        'odoo14-addon-account_payment_paired_internal_transfer',
        'odoo14-addon-account_payment_return',
        'odoo14-addon-account_payment_return_import',
        'odoo14-addon-account_payment_return_import_iso20022',
        'odoo14-addon-account_payment_term_discount',
        'odoo14-addon-account_payment_term_extension',
        'odoo14-addon-account_payment_terminal',
        'odoo14-addon-account_payment_view_check_number',
        'odoo14-addon-account_payment_widget_amount',
        'odoo14-addon-partner_aging',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 14.0',
    ]
)
