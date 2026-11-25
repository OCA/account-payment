Usage
=====

Once the module is installed, companies configured to use automatic payment
notifications are processed periodically by the scheduled action.

For each company, the scheduled action performs the following steps:

* Retrieves the payment notification domain configured for the company.
* Applies the fixed payment selection criteria.
* Searches for payments matching the resulting domain.
* Marks the matching payments as sent.
* Uses the notification mechanism provided by
  ``account_payment_notification``.

Only companies configured with automatic payment notifications are processed.

Payment selection
-----------------

The module combines a fixed domain with the domain configured by the user.

The fixed criteria ensure that:

* the payment is not in ``draft`` or ``cancel`` state;
* the payment belongs to the current company;
* the payment has not already been sent;
* the payment date is greater than or equal to the configured notification
  start date, when one is defined.

The additional domain allows each company to define which payments should be
included in the automatic notification process.

For example, a company could configure a domain such as:

::

   [('partner_type', '=', 'customer')]

The configured domain is combined with the fixed criteria automatically.

Notifications
-------------

The module does not implement its own email or SMS notification mechanism.

After selecting the payments, it calls the existing
``account_payment_notification`` payment notification flow.

The notification method configured in the company settings is therefore used,
including the email and SMS notification methods supported by the base module.

Payments are only processed while ``is_sent`` is false, preventing the
scheduled action from notifying the same payment repeatedly.