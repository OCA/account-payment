[![Runbot Status](https://runbot.odoo-community.org/runbot/badge/flat/96/10.0.svg)](https://runbot.odoo-community.org/runbot/repo/github-com-oca-account-payment-96)
[![Build Status](https://travis-ci.org/OCA/account-payment.svg?branch=10.0)](https://travis-ci.org/OCA/account-payment)
[![Coverage Status](https://coveralls.io/repos/OCA/account-payment/badge.png?branch=10.0)](https://coveralls.io/r/OCA/account-payment?branch=10.0)

Odoo account payment modules
============================

This project includes modules that handle payment related tasks:

* Manage payment modes like the official ones Paypal. Ogone...
* Easy the visualization of payment related stuff.
* Modules that modifies the flow involved in the payment.
* ...

You can find complementary modules for handling bank payment related tasks on:

 * https://github.com/OCA/bank-payment
 
[//]: # (addons)

Available addons
----------------
addon | version | summary
--- | --- | ---
[account_cash_discount_base](account_cash_discount_base/) | 10.0.1.0.0 | Account Cash Discount Base
[account_cash_discount_payment](account_cash_discount_payment/) | 10.0.1.0.0 | Account Cash Discount Payment
[account_cash_discount_write_off](account_cash_discount_write_off/) | 10.0.1.0.0 | Create an automatic writeoff for payment with discount on the payment order confirmation
[account_check_printing_report_base](account_check_printing_report_base/) | 10.0.1.2.0 | Account Check Printing Report Base
[account_check_printing_report_dlt103](account_check_printing_report_dlt103/) | 10.0.1.0.0 | Account Check Printing Report DLT103
[account_check_printing_report_sslm102](account_check_printing_report_sslm102/) | 10.0.1.0.0 | Allows you to print SSLM102 lined checks.
[account_check_report](account_check_report/) | 10.0.1.0.0 | Account Check Report
[account_due_list](account_due_list/) | 10.0.2.0.0 | Payments Due list
[account_due_list_aging_comments](account_due_list_aging_comments/) | 10.0.1.0.0 | Payments Due list aging comments
[account_due_list_days_overdue](account_due_list_days_overdue/) | 10.0.0.1.0 | Payments Due list days overdue
[account_due_list_payment_mode](account_due_list_payment_mode/) | 10.0.1.0.0 | Payment due list with payment mode
[account_move_line_auto_reconcile_hook](account_move_line_auto_reconcile_hook/) | 10.0.1.0.0 | Adds Hook to account move line
[account_partner_reconcile](account_partner_reconcile/) | 10.0.1.0.0 | Account Partner Reconcile
[account_payment_batch_process](account_payment_batch_process/) | 10.0.1.0.1 | Process Payments in Batch
[account_payment_credit_card](account_payment_credit_card/) | 10.0.1.0.0 | Add support for credit card payments
[account_payment_residual_amount](account_payment_residual_amount/) | 10.0.1.0.0 | Extends the view of payments to show the residual amount (amount that has not yet been reconciled)
[account_payment_return](account_payment_return/) | 10.0.1.1.1 | Manage the return of your payments
[account_payment_return_import](account_payment_return_import/) | 10.0.1.0.0 | This module adds a generic wizard to import payment returnfile formats. Is only the base to be extended by anothermodules
[account_payment_return_import_sepa_pain](account_payment_return_import_sepa_pain/) | 10.0.1.0.0 | Module to import SEPA Direct Debit Unpaid Report File Format PAIN.002.001.03
[account_payment_show_invoice](account_payment_show_invoice/) | 10.0.1.1.0 | Extends the tree view of payments to show the paid invoices related to the payments using the vendor reference by default
[account_payment_widget_amount](account_payment_widget_amount/) | 10.0.1.0.0 | Extends the payment widget to be able to choose the payment amount
[partner_aging](partner_aging/) | 10.0.1.0.0 | Aging as a view - invoices and credits


Unported addons
---------------
addon | version | summary
--- | --- | ---
[account_vat_on_payment](account_vat_on_payment/) | 8.0.1.0.0 (unported) | VAT on payment

[//]: # (end addons)
