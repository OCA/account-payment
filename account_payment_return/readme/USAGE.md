1.  Go to Invoicing \> Customers \> Customer Payment Returns, and create
    a new record, register on each line a paid (reconciled) receivable
    journal item, and input the amount that is going to be returned.

    Another option to fill info is setting references and click match
    button to find matching payment journal items. This
    functionality is extended by other modules as
    *account_payment_return_import_sepa_pain*

    Matching looks for the reference or payment reference on the journal entry,
    within the return's company and for the selected customer, if any. An invoice
    number only matches when it is recorded in one of these payment references.
    Unmatched lines remain pending for manual selection or an importer extension.
    When several payment lines match, select the payment reference manually or
    use a unique reference; the module does not choose a payment arbitrarily.

2.  It's possible to add bank charges amount on each line.

3.  Next, press button "Confirm" to create a new move line that removes
    the balance from the bank journal and reconcile items together to
    show payment history through it.

4.  After confirmation you can access from the payment form view to the
    move created.
