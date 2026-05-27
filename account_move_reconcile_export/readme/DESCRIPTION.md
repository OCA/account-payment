This module adds a computed field `reconciled_move_ids` ("Reconciled Moves") on
journal entries, which allows you to export information related to the moves
reconciled against an invoice. For example, you can export the dates and amounts
of each payment linked to an invoice.

Out of the box, Odoo does not expose an easily exportable field for this data —
the existing payments widget is explicitly marked as ``exportable=False``.
