
[![Runboat](https://img.shields.io/badge/runboat-Try%20me-875A7B.png)](https://runboat.odoo-community.org/builds?repo=OCA/account-payment&target_branch=13.0)
[![Pre-commit Status](https://github.com/OCA/account-payment/actions/workflows/pre-commit.yml/badge.svg?branch=13.0)](https://github.com/OCA/account-payment/actions/workflows/pre-commit.yml?query=branch%3A13.0)
[![Build Status](https://github.com/OCA/account-payment/actions/workflows/test.yml/badge.svg?branch=13.0)](https://github.com/OCA/account-payment/actions/workflows/test.yml?query=branch%3A13.0)
[![codecov](https://codecov.io/gh/OCA/account-payment/branch/13.0/graph/badge.svg)](https://codecov.io/gh/OCA/account-payment)
[![Translation Status](https://translation.odoo-community.org/widgets/account-payment-13-0/-/svg-badge.svg)](https://translation.odoo-community.org/engage/account-payment-13-0/?utm_source=widget)

<!-- /!\ do not modify above this line -->

# Odoo account payment modules

This project includes modules that handle payment related tasks:

* Manage payment modes like the official ones Paypal. Ogone...
* Easy the visualization of payment related stuff.
* Modules that modifies the flow involved in the payment.
* ...

You can find complementary modules for handling bank payment related tasks on:

 * https://github.com/OCA/bank-payment

<!-- /!\ do not modify below this line -->

<!-- prettier-ignore-start -->

[//]: # (addons)

Available addons
----------------
addon | version | maintainers | summary
--- | --- | --- | ---
[account_cash_discount_base](account_cash_discount_base/) | 13.0.1.0.0 |  | Account Cash Discount Base
[account_cash_discount_payment](account_cash_discount_payment/) | 13.0.1.0.0 |  | Account Cash Discount Payment
[account_cash_discount_write_off](account_cash_discount_write_off/) | 13.0.1.0.0 |  | Create an automatic writeoff for payment with discount on the payment order confirmation
[account_cash_invoice](account_cash_invoice/) | 13.0.1.0.1 |  | Pay and receive invoices from bank statements
[account_check_date](account_check_date/) | 13.0.1.0.0 |  | Add check date on payment for check printing
[account_check_printing_report_base](account_check_printing_report_base/) | 13.0.2.1.2 |  | Account Check Printing Report Base
[account_due_list](account_due_list/) | 13.0.2.0.1 |  | List of open credits and debits, with due date
[account_due_list_days_overdue](account_due_list_days_overdue/) | 13.0.1.0.2 |  | Payments Due list days overdue
[account_due_list_payment_mode](account_due_list_payment_mode/) | 13.0.2.0.0 |  | Payment Due List Payment Mode
[account_payment_multi_deduction](account_payment_multi_deduction/) | 13.0.1.1.1 | [![kittiu](https://github.com/kittiu.png?size=30px)](https://github.com/kittiu) | Payment Register with Multiple Deduction
[account_payment_promissory_note](account_payment_promissory_note/) | 13.0.1.1.1 |  | Account Payment Promissory Note
[account_payment_return](account_payment_return/) | 13.0.1.0.6 |  | Manage the return of your payments
[account_payment_return_import](account_payment_return_import/) | 13.0.1.0.4 |  | This module adds a generic wizard to import payment returnfile formats. Is only the base to be extended by anothermodules
[account_payment_return_import_iso20022](account_payment_return_import_iso20022/) | 13.0.1.0.0 |  | This addon allows to import payment returns from ISO 20022 files like PAIN or CAMT.
[account_payment_show_invoice](account_payment_show_invoice/) | 13.0.1.0.1 |  | Extends the tree view of payments to show the paid invoices related to the payments using the vendor reference by default
[account_payment_term_extension](account_payment_term_extension/) | 13.0.3.0.6 |  | Adds rounding, months, weeks and multiple payment days properties on payment term lines
[account_payment_term_partner_holiday](account_payment_term_partner_holiday/) | 13.0.1.2.1 | [![victoralmau](https://github.com/victoralmau.png?size=30px)](https://github.com/victoralmau) | Account Payment Term Partner Holiday
[account_payment_term_security](account_payment_term_security/) | 13.0.1.0.0 |  | Payment Term Security
[partner_aging](partner_aging/) | 13.0.1.0.1 | [![smangukiya](https://github.com/smangukiya.png?size=30px)](https://github.com/smangukiya) | Aging as a view - invoices and credits
[sale_payment_mgmt](sale_payment_mgmt/) | 13.0.1.0.1 | [![victoralmau](https://github.com/victoralmau.png?size=30px)](https://github.com/victoralmau) | List and create customer payments for salesmen

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
