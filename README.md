
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
[account_cash_discount_payment](account_cash_discount_payment/) | 14.0.1.0.1 |  | Account Cash Discount Payment
[account_cash_discount_write_off](account_cash_discount_write_off/) | 14.0.1.0.0 |  | Create an automatic writeoff for payment with discount on the payment order confirmation
[account_cash_invoice](account_cash_invoice/) | 14.0.1.2.0 |  | Pay and receive invoices from bank statements
[account_due_list](account_due_list/) | 14.0.1.0.0 |  | List of open credits and debits, with due date
[account_due_list_aging_comment](account_due_list_aging_comment/) | 14.0.1.0.0 |  | Account Due List Aging Comment
[account_due_list_days_overdue](account_due_list_days_overdue/) | 14.0.1.0.0 |  | Payments Due list days overdue
[account_due_list_payment_mode](account_due_list_payment_mode/) | 14.0.1.0.0 |  | Payment Due List Payment Mode
[account_payment_batch_process](account_payment_batch_process/) | 14.0.1.0.0 |  | Account Batch Payments Processing for Customers Invoices and Supplier Invoices
[account_payment_batch_process_discount](account_payment_batch_process_discount/) | 14.0.1.0.0 | [![mgosai](https://github.com/mgosai.png?size=30px)](https://github.com/mgosai) | Discount on batch payments
[account_payment_credit_card](account_payment_credit_card/) | 14.0.1.0.1 | [![max3903](https://github.com/max3903.png?size=30px)](https://github.com/max3903) | Add support for credit card payments
[account_payment_multi_deduction](account_payment_multi_deduction/) | 14.0.1.1.0 | [![kittiu](https://github.com/kittiu.png?size=30px)](https://github.com/kittiu) | Payment Register with Multiple Deduction
[account_payment_paired_internal_transfer](account_payment_paired_internal_transfer/) | 14.0.1.0.0 |  | Crete internal transfers in one move.
[account_payment_return](account_payment_return/) | 14.0.1.0.4 |  | Manage the return of your payments
[account_payment_return_import](account_payment_return_import/) | 14.0.1.0.2 |  | This module adds a generic wizard to import payment returnfile formats. Is only the base to be extended by anothermodules
[account_payment_return_import_iso20022](account_payment_return_import_iso20022/) | 14.0.1.0.0 |  | This addon allows to import payment returns from ISO 20022 files like PAIN or CAMT.
[account_payment_term_discount](account_payment_term_discount/) | 14.0.1.1.7 | [![bodedra](https://github.com/bodedra.png?size=30px)](https://github.com/bodedra) | Account Payment Terms Discount
[account_payment_term_extension](account_payment_term_extension/) | 14.0.1.0.3 |  | Adds rounding, months, weeks and multiple payment days properties on payment term lines
[account_payment_terminal](account_payment_terminal/) | 14.0.1.0.0 | [![sbejaoui](https://github.com/sbejaoui.png?size=30px)](https://github.com/sbejaoui) | This addon allows to pay invoices using payment terminal
[account_payment_view_check_number](account_payment_view_check_number/) | 14.0.1.0.0 |  | Account Payment View Check Number
[account_payment_widget_amount](account_payment_widget_amount/) | 14.0.1.0.0 | [![ChrisOForgeFlow](https://github.com/ChrisOForgeFlow.png?size=30px)](https://github.com/ChrisOForgeFlow) | Extends the payment widget to be able to choose the payment amount
[partner_aging](partner_aging/) | 14.0.1.0.2 | [![smangukiya](https://github.com/smangukiya.png?size=30px)](https://github.com/smangukiya) | Aging as a view - invoices and credits

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
