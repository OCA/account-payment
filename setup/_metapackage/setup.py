import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo10-addons-oca-account-payment",
    description="Meta package for oca-account-payment Odoo addons",
    version=version,
    install_requires=[
        'odoo10-addon-account_cash_discount_base',
        'odoo10-addon-account_cash_discount_payment',
        'odoo10-addon-account_cash_discount_write_off',
        'odoo10-addon-account_check_printing_report_base',
        'odoo10-addon-account_check_printing_report_dlt103',
        'odoo10-addon-account_check_printing_report_sslm102',
        'odoo10-addon-account_check_report',
        'odoo10-addon-account_due_list',
        'odoo10-addon-account_due_list_aging_comments',
        'odoo10-addon-account_due_list_days_overdue',
        'odoo10-addon-account_due_list_payment_mode',
        'odoo10-addon-account_move_line_auto_reconcile_hook',
        'odoo10-addon-account_partner_reconcile',
        'odoo10-addon-account_payment_batch_process',
        'odoo10-addon-account_payment_credit_card',
        'odoo10-addon-account_payment_residual_amount',
        'odoo10-addon-account_payment_return',
        'odoo10-addon-account_payment_return_import',
        'odoo10-addon-account_payment_return_import_sepa_pain',
        'odoo10-addon-account_payment_show_invoice',
        'odoo10-addon-account_payment_widget_amount',
        'odoo10-addon-partner_aging',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
