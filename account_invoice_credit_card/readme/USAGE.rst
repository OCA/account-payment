Manually add a Credit Card to a Customer,
and store the tokenized details allowing to use in in payment transactions:

* On the Partner form, or in an Invoice, click on the "Add ePayment Method" button,
  and fill in the credit card details.
* On the Partner form, the "Saved Payment Data" smart button gives access
  to the saved tokens.

The credit card information stored is:

* The Payment Acquirer used.
* The payment token genereated by the payment provider.
* The last four digits of the credit card.
* The expirity date.

A saved payment token can be set as the default,
for example to be used in automatic payment processes.
The selected default is available in the Partner form / Accounting tab,
in the "Electronic Payment Method" section.


To pay an Invoice using a stored Credit Card,
or equivalent electronic payment token:

* On an open Invoice, select the "Payment" button and
  choose the Journal for the payment acquirer to be used.
* Then select the "Electronic" option and
  pick the payment token from the list of saved ones.

Multiple invoices can be paid using the save Credit Card saved token.
The invoices selected must be open, and share the same payment processor.
To use this:

* On the Invoice list, select the Invoices to pay.
* On the Action menu select the "Register Payments" option.

In Batch Payment using a credit card, a payment confirmation will done
through cron job named 'Post process payment transactions'.
