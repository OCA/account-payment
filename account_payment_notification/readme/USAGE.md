To use this module, you need to:

1.  Go to *Invoicing* or *Accounting* app.
2.  Go to *Customers \> Payments* or *Vendors \> Payments*.
3.  Select one or more payments.
4.  Click on *Action*.
5.  Select *Notify partners*.

Odoo will use your preferred notification method, as defined in
configuration (see that section), to notify all the chosen partners.

Both email and SMS notifications are put in outgoing queues. They will
be cleared automatically when their corresponding cron jobs are
executed.

If you do that same operation from a payment form view, you will have
the option to choose between sending an email or an SMS. You will be
able to edit the template before sending it.

💡 Tip: You have new filters in the payments list. Use them to select
those that have (or not) email or mobile phone.

⚠️ [Sending SMS is a paid
service](https://www.odoo.com/documentation/15.0/applications/marketing/sms_marketing/pricing/pricing_and_faq.html).
