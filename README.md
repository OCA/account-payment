[![Runbot Status](https://runbot.odoo-community.org/runbot/badge/flat/96/13.0.svg)](https://runbot.odoo-community.org/runbot/repo/github-com-oca-account-payment-96)
[![Build Status](https://travis-ci.com/OCA/account-payment.svg?branch=13.0)](https://travis-ci.com/OCA/account-payment)
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
addon | version | summary
--- | --- | ---
[account_check_date](account_check_date/) | 13.0.1.0.0 | Add check date on payment for check printing
[account_check_printing_report_base](account_check_printing_report_base/) | 13.0.2.0.1 | Account Check Printing Report Base
[account_due_list](account_due_list/) | 13.0.2.0.0 | List of open credits and debits, with due date
[account_due_list_days_overdue](account_due_list_days_overdue/) | 13.0.1.0.1 | Payments Due list days overdue
[account_due_list_payment_mode](account_due_list_payment_mode/) | 13.0.2.0.0 | Payment Due List Payment Mode
[account_payment_multi_deduction](account_payment_multi_deduction/) | 13.0.1.1.0 | Payment Register with Multiple Deduction
[account_payment_promissory_note](account_payment_promissory_note/) | 13.0.1.0.0 | Account Payment Promissory Note
[account_payment_return](account_payment_return/) | 13.0.1.0.2 | Manage the return of your payments
[account_payment_return_import](account_payment_return_import/) | 13.0.1.0.2 | This module adds a generic wizard to import payment returnfile formats. Is only the base to be extended by anothermodules
[account_payment_return_import_iso20022](account_payment_return_import_iso20022/) | 13.0.1.0.0 | This addon allows to import payment returns from ISO 20022 files like PAIN or CAMT.
[account_payment_term_extension](account_payment_term_extension/) | 13.0.3.0.4 | Adds rounding, months, weeks and multiple payment days properties on payment term lines
[partner_aging](partner_aging/) | 13.0.1.0.0 | Aging as a view - invoices and credits
[sale_payment_mgmt](sale_payment_mgmt/) | 13.0.1.0.0 | List and create customer payments for salesmen

[//]: # (end addons)

<!-- prettier-ignore-end -->

## Licenses

This repository is licensed under [AGPL-3.0](LICENSE).

However, each module can have a totally different license, as long as they adhere to OCA
policy. Consult each module's `__manifest__.py` file, which contains a `license` key
that explains its license.

----

OCA, or the [Odoo Community Association](http://odoo-community.org/), is a nonprofit
organization whose mission is to support the collaborative development of Odoo features
and promote its widespread use.
