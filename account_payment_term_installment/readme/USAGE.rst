#. Go to *Accounting > Configuration > Payment Terms*.
#. Open or create a payment term.
#. Set the **Number of Installments** field to the desired value.
#. Optionally adjust the **Days Between Installments** (default 30).
#. The terms list is regenerated as equal installments plus a final balance line.

.. warning::

   Setting **Number of Installments** greater than 1 replaces the existing
   payment term lines. Per-line customizations added by other modules
   (e.g. ``account_payment_term_extension`` end-of-month/days-after fields,
   ``account_payment_term_discount`` discount fields,
   ``account_payment_term_partner_holiday`` holiday data) are not preserved
   and must be reapplied after generation.
