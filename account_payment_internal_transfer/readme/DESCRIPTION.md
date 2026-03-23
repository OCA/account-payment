This module restores the internal transfer functionality for payments that was
available in previous Odoo versions but was removed.

Now the recommended approach for internal transfers requires waiting for
bank statement lines to be imported and then using reconciliation models. This
workflow has significant drawbacks:

- Users cannot register transfers at the moment they occur
- There is a risk of forgetting unreconciled transactions if bank statements
  are delayed
- Users without direct bank access have no way to track pending transfers
- The workflow is tedious and error-prone

This module allows users to register internal transfers immediately when they
happen, creating the intermediate journal entries with outstanding accounts.
Later, when bank statements are imported, each side can be reconciled
independently. This results in 4 journal entries total (2 payments + 2 bank
statement reconciliations).

**Features:**

- Create internal transfers directly from the Accounting Dashboard
- A paired payment is automatically created in the destination journal
- Their journal entries are automatically reconciled
- Proper labels are set on journal items for easy identification
- Cancel and reset to draft cascades to the paired payment
- Deleting a transfer also deletes the paired payment
- Search filter to easily find internal transfers in the payments list
