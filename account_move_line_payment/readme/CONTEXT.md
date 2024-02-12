This module was developed because in the invoices list view, Odoo only displays
the due date of each invoice's last payment. However, most times you only need
to know which payments are due *today*, even if there's a later payment for
that invoice.

At the same time, if you register a partial payment, Odoo will match it only
partially, even when that was the expected payment due.

When there are a lot of partial payments, it becomes impossible to handle
manually without a module like this one.
