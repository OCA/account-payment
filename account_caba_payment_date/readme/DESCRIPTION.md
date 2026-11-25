This module sets the date of the tax cash basis (CABA) journal entry to the
real payment date instead of the date Odoo chooses.

Standard Odoo dates the cash basis entry with the newest date of the
reconciled entries, and, when that date falls in a locked period, with the
date of the day the reconciliation is done. This shifts the cash basis
taxes (e.g. VAT effectively paid) to a fiscal month different from the
payment month, which is not acceptable in countries where those taxes are
due on the payment date (e.g. Mexico).

With this module the cash basis entry is always dated on the date of the
bank/cash entry of the reconciliation. When that date falls in a locked
period, the behavior is configurable per company:

- **Block the reconciliation** (default): raise an error asking to reopen
  the period.
- **Use the first open date**: date the entry on the first day after the
  lock date.
- **Keep the standard behavior**: let Odoo date the entry on the
  reconciliation date.
