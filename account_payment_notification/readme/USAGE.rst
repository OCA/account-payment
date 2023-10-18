To use this module, you need to:

#. Go to *Invoicing* or *Accounting* app.
#. Go to *Customers > Payments* or *Vendors > Payments*.
#. Select one or more payments.
#. Click on *Action*.
#. Select *Notify partners*.

Odoo will use your preferred notification method, as defined in
configuration (see that section), to notify all the chosen partners.

Emailnotifications are put in outgoing queues. They will be
cleared automatically when their corresponding cron jobs are executed.

If you do that same operation from a payment form view, you will have the option
to choose between sending an email. You will be able to edit the
template before sending it.

💡 Tip: You have new filters in the payments list. Use them to select those
that have (or not) email or mobile phone.
