To send notifications manually, you need to:

1.  Go to *Invoicing* or *Accounting* app.
2.  Go to *Customers \> Payments* or *Vendors \> Payments*.
3.  Select one or more payments.
4.  Click on *Action*.
5.  Select *Notify partners*.

Odoo will use your preferred notification method, as defined in
configuration (see that section), to notify all the chosen partners.

> [!TIP]
> You have new filters in the payments list. Use them to select
> those that have (or not) email or mobile phone.

Both email and SMS notifications are put in outgoing queues if done massively.
In that case, they will be cleared automatically when their corresponding cron
jobs are executed.

> [!WARNING]
> [Sending SMS is a paid service](https://www.odoo.com/documentation/15.0/applications/marketing/sms_marketing/pricing/pricing_and_faq.html).

If you do that same operation from a payment form view, you will have
the option to choose between sending an email or an SMS. You will be
able to edit the template before sending it.

> [!NOTE]
> Sometimes notifications will be registered as notes, and sometimes as messages,
> depending on whether they are sent in bulk or individually. In any case, they
> are notified to the partner.

To send notifications automatically, you need to:
1.  Go to *Invoicing* or *Accounting* app.
2.  Go to *Customers \> Payments* or *Vendors \> Payments*.
3.  Open one paymnt.
4.  Click on *Mark as Sent*.

> [!TIP]
> Odoo EE has a module named `account_batch_payment` that automates that.
> If you use it, payment notifications will be queued when sent.
