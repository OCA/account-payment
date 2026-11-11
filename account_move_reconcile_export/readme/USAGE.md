Create a export template like:

- Number (name)
- Due Date (invoice_date_due)
- Reconciled Moves (reconciled_move_ids)
- Reconciled Moves/Journal (reconciled_move_ids/journal_id)
- Reconciled Moves/Date (reconciled_move_ids/date)
- Reconciled Moves/Payments/Amount (reconciled_move_ids/payment_ids/amount)

Will return the next result:

| **Number**  | **Due Date** | **Reconciled Moves**       | **Reconciled Moves/Date** | **Reconciled Moves/Journal** | **Reconciled Moves/Payments/Amount** |
| :---------------- | :----------------- | :------------------------------- | :------------------------------ | :--------------------------------- | :----------------------------------------- |
| BILL/2025/01/0001 | 2026-04-22         | PBNK1/2026/00003 (INV/2025/0057) | 2026-04-22                      | Bank                               | 300,00                                     |
|                   |                    | PBNK1/2026/00004 (INV/2025/0057) | 2026-04-23                      | Bank                               | 322,27                                     |
