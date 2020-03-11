* Activate payment acquirer named IPPay ACH
* Add API URL and API TerminalId in Ippay config. 
* Configure journal for it and allow it to make electronic payments.

    * Type: Bank
    * Advanced Settings /payment Method Types, for Incoming Payments:
      select Electronic
    * Advanced Settings /payment Method Types, for Outgoing Payments:
      select Checks (needed for the Sequence field to be made visible)
