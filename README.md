
[![Runboat](https://img.shields.io/badge/runboat-Try%20me-875A7B.png)](https://runboat.odoo-community.org/builds?repo=OCA/account-payment&target_branch=14.0)
[![Pre-commit Status](https://github.com/OCA/account-payment/actions/workflows/pre-commit.yml/badge.svg?branch=14.0)](https://github.com/OCA/account-payment/actions/workflows/pre-commit.yml?query=branch%3A14.0)
[![Build Status](https://github.com/OCA/account-payment/actions/workflows/test.yml/badge.svg?branch=14.0)](https://github.com/OCA/account-payment/actions/workflows/test.yml?query=branch%3A14.0)
[![codecov](https://codecov.io/gh/OCA/account-payment/branch/14.0/graph/badge.svg)](https://codecov.io/gh/OCA/account-payment)
[![Translation Status](https://translation.odoo-community.org/widgets/account-payment-14-0/-/svg-badge.svg)](https://translation.odoo-community.org/engage/account-payment-14-0/?utm_source=widget)

<!-- /!\ do not modify above this line -->

# Odoo account payment modules

This project includes modules that handle payment related tasks

<!-- /!\ do not modify below this line -->

<!-- prettier-ignore-start -->

[//]: # (addons)

Available addons
----------------
addon | version | maintainers | summary
--- | --- | --- | ---
[account_cash_discount_base](account_cash_discount_base/) | 14.0.1.0.0 |  | Account Cash Discount Base
[account_cash_discount_payment](account_cash_discount_payment/) | 14.0.1.0.2 |  | Account Cash Discount Payment
[account_cash_discount_reconcile_write_off](account_cash_discount_reconcile_write_off/) | 14.0.1.0.0 |  | Account Cash Discount Reconciliation Write off display
[account_cash_discount_write_off](account_cash_discount_write_off/) | 14.0.1.0.0 |  | Create an automatic writeoff for payment with discount on the payment order confirmation
[account_cash_invoice](account_cash_invoice/) | 14.0.1.3.0 |  | Pay and receive invoices from bank statements
[account_check_date](account_check_date/) | 14.0.1.0.0 | <a href='https://github.com/ps-tubtim'><img src='https://github.com/ps-tubtim.png' width='32' height='32' style='border-radius:50%;' alt='ps-tubtim'/></a> | Add check date on payment for check printing
[account_check_payee](account_check_payee/) | 14.0.1.0.0 | <a href='https://github.com/ps-tubtim'><img src='https://github.com/ps-tubtim.png' width='32' height='32' style='border-radius:50%;' alt='ps-tubtim'/></a> | Add payee on payment for check printing
[account_check_printing_report_base](account_check_printing_report_base/) | 14.0.1.0.0 |  | Account Check Printing Report Base
[account_check_printing_report_sslm102](account_check_printing_report_sslm102/) | 14.0.1.0.1 |  | Allows you to print SSLM102 lined checks.
[account_due_list](account_due_list/) | 14.0.1.2.0 |  | List of open credits and debits, with due date
[account_due_list_aging_comment](account_due_list_aging_comment/) | 14.0.1.0.0 |  | Account Due List Aging Comment
[account_due_list_days_overdue](account_due_list_days_overdue/) | 14.0.1.0.0 |  | Payments Due list days overdue
[account_due_list_edit_inline](account_due_list_edit_inline/) | 14.0.1.0.0 |  | Account List Inline Edit
[account_due_list_payment](account_due_list_payment/) | 14.0.1.0.1 |  | Allows you to make payments directly from the due list view
[account_due_list_payment_mode](account_due_list_payment_mode/) | 14.0.1.0.0 |  | Payment Due List Payment Mode
[account_financial_discount](account_financial_discount/) | 14.0.1.0.1 | <a href='https://github.com/grindtildeath'><img src='https://github.com/grindtildeath.png' width='32' height='32' style='border-radius:50%;' alt='grindtildeath'/></a> | Handle financial discounts for early payments
[account_payment_batch_process](account_payment_batch_process/) | 14.0.1.2.0 |  | Account Batch Payments Processing for Customers Invoices and Supplier Invoices
[account_payment_batch_process_discount](account_payment_batch_process_discount/) | 14.0.1.0.1 | <a href='https://github.com/mgosai'><img src='https://github.com/mgosai.png' width='32' height='32' style='border-radius:50%;' alt='mgosai'/></a> | Discount on batch payments
[account_payment_credit_card](account_payment_credit_card/) | 14.0.1.0.2 | <a href='https://github.com/max3903'><img src='https://github.com/max3903.png' width='32' height='32' style='border-radius:50%;' alt='max3903'/></a> | Add support for credit card payments
[account_payment_line](account_payment_line/) | 14.0.1.0.0 | <a href='https://github.com/ChrisOForgeFlow'><img src='https://github.com/ChrisOForgeFlow.png' width='32' height='32' style='border-radius:50%;' alt='ChrisOForgeFlow'/></a> | Payment Counterpart Lines
[account_payment_line_import](account_payment_line_import/) | 14.0.1.0.0 | <a href='https://github.com/ChrisOForgeFlow'><img src='https://github.com/ChrisOForgeFlow.png' width='32' height='32' style='border-radius:50%;' alt='ChrisOForgeFlow'/></a> | Payment Counterpart Lines Import XLSX
[account_payment_multi_deduction](account_payment_multi_deduction/) | 14.0.1.1.0 | <a href='https://github.com/kittiu'><img src='https://github.com/kittiu.png' width='32' height='32' style='border-radius:50%;' alt='kittiu'/></a> | Payment Register with Multiple Deduction
[account_payment_paired_internal_transfer](account_payment_paired_internal_transfer/) | 14.0.1.0.1 |  | Crete internal transfers in one move.
[account_payment_promissory_note](account_payment_promissory_note/) | 14.0.1.0.0 |  | Account Payment Promissory Note
[account_payment_register_keep_amount](account_payment_register_keep_amount/) | 14.0.1.0.0 |  | Keep set amount during Payment registration.
[account_payment_return](account_payment_return/) | 14.0.1.0.7 |  | Manage the return of your payments
[account_payment_return_import](account_payment_return_import/) | 14.0.1.0.2 |  | This module adds a generic wizard to import payment returnfile formats. Is only the base to be extended by anothermodules
[account_payment_return_import_iso20022](account_payment_return_import_iso20022/) | 14.0.2.0.1 |  | This addon allows to import payment returns from ISO 20022 files like PAIN or CAMT.
[account_payment_term_discount](account_payment_term_discount/) | 14.0.1.1.7 | <a href='https://github.com/bodedra'><img src='https://github.com/bodedra.png' width='32' height='32' style='border-radius:50%;' alt='bodedra'/></a> | Account Payment Terms Discount
[account_payment_term_extension](account_payment_term_extension/) | 14.0.1.0.3 |  | Adds rounding, months, weeks and multiple payment days properties on payment term lines
[account_payment_term_partner_holiday](account_payment_term_partner_holiday/) | 14.0.1.0.0 | <a href='https://github.com/victoralmau'><img src='https://github.com/victoralmau.png' width='32' height='32' style='border-radius:50%;' alt='victoralmau'/></a> | Account Payment Term Partner Holiday
[account_payment_terminal](account_payment_terminal/) | 14.0.1.0.0 | <a href='https://github.com/sbejaoui'><img src='https://github.com/sbejaoui.png' width='32' height='32' style='border-radius:50%;' alt='sbejaoui'/></a> | This addon allows to pay invoices using payment terminal
[account_payment_view_check_number](account_payment_view_check_number/) | 14.0.1.0.0 |  | Account Payment View Check Number
[account_payment_widget_amount](account_payment_widget_amount/) | 14.0.1.0.1 | <a href='https://github.com/ChrisOForgeFlow'><img src='https://github.com/ChrisOForgeFlow.png' width='32' height='32' style='border-radius:50%;' alt='ChrisOForgeFlow'/></a> | Extends the payment widget to be able to choose the payment amount
[partner_aging](partner_aging/) | 14.0.1.0.4 | <a href='https://github.com/smangukiya'><img src='https://github.com/smangukiya.png' width='32' height='32' style='border-radius:50%;' alt='smangukiya'/></a> | Aging as a view - invoices and credits
[partner_restrict_payment_acquirer](partner_restrict_payment_acquirer/) | 14.0.1.0.0 | <a href='https://github.com/geomer198'><img src='https://github.com/geomer198.png' width='32' height='32' style='border-radius:50%;' alt='geomer198'/></a> <a href='https://github.com/CetmixGitDrone'><img src='https://github.com/CetmixGitDrone.png' width='32' height='32' style='border-radius:50%;' alt='CetmixGitDrone'/></a> | Partner Restrict Payment Acquirer
[product_restrict_payment_acquirer](product_restrict_payment_acquirer/) | 14.0.1.0.0 | <a href='https://github.com/bearnard21'><img src='https://github.com/bearnard21.png' width='32' height='32' style='border-radius:50%;' alt='bearnard21'/></a> <a href='https://github.com/CetmixGitDrone'><img src='https://github.com/CetmixGitDrone.png' width='32' height='32' style='border-radius:50%;' alt='CetmixGitDrone'/></a> | Product Restrict Payment Acquirer

[//]: # (end addons)

<!-- prettier-ignore-end -->

## Licenses

This repository is licensed under [AGPL-3.0](LICENSE).

However, each module can have a totally different license, as long as they adhere to Odoo Community Association (OCA)
policy. Consult each module's `__manifest__.py` file, which contains a `license` key
that explains its license.

----
OCA, or the [Odoo Community Association](http://odoo-community.org/), is a nonprofit
organization whose mission is to support the collaborative development of Odoo features
and promote its widespread use.
