This module change the date of the CABA move to the day of the payment.

This module is required to fix the following use case:

Create a payment at day 1 of the month
Create an invoice at day 15 of the month

The CABA move will be created at day 15 of the month,
but it needs to be the day of the payment to comply with the fiscal requirements.
