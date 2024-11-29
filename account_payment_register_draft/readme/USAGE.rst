To use this module, follow these steps:

1. Configure the payment settings as needed (e.g., set payments to start in the Draft state).
2. After configuration, you can register a payment. The payment will initially be set to the Draft state.
    - The reconcile move line will be keep in the `to_auto_reconcile` field.
    - Once the payment is confirmed, the `to_auto_reconcile` field will be cleared, and the payment will proceed to the finalized state.
