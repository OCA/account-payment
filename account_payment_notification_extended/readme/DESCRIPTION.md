Account Payment Notification Extended
=====================================

This module extends the ``account_payment_notification`` module to support
automatic payment notifications based on company-specific configuration.

It adds a scheduled process that selects payments according to a configurable
domain and notifies them using the notification mechanisms provided by the
``account_payment_notification`` module.

The selection is restricted to payments that:

* are not in ``draft`` or ``cancel`` state;
* belong to the company being processed;
* have not been sent yet;
* meet the configured notification start date, when defined;
* match the additional domain configured by the user.

The module reuses the existing notification methods and templates provided by
``account_payment_notification`` and does not introduce a separate
notification mechanism.