.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

====================
Credit Card Payments
====================

This module provides a way to record Credit Card purchases and to pay them the same way regular purchases are recorded (via Vendor Bills) and paid (via Vendor Payments).

By default, if vendor bills are used to record credit card purchases, the liability (AP) from the supplier/vendor must be moved to the credit card company via a manual journal entry.

Because a journal entry contains less information than a vendor bill, there may be a loss of information that affects book keeping accuracy and the ability to properly reconcile the AP amount when the credit card statement arrives and needs to be settled.
This method also requires an additional step not needed when a vendor bill is paid via bank or cash.

This module automates the creation of the manual journal entry required to move the AP to the credit card company, retains all information about the purchase in an invoice document, and leverages the standard purchase and payment workflow already in place for bank and cash payments.

It supports as many Credit Cards as are needed, configured in the same way an additional payment method would be (i.e. via the creation of a new journal).

To settle a Credit Card statement, the regular workflow to record a vendor payment is used – allowing the removal of charges not included in the statement.
Non-purchase transactions like fees for annual membership, balance transfers, cash advances and foreign transactions; as well as charges for late payments and returned checks; can be entered either as Vendor Invoices or manual Journal Entries as users elect.

Both of these methods will allow these items to be settled when making a payment to the credit card company.

This module also supports payment cancellation and re-entry (in the case a mistaken amount is entered) as well as refunds (where the purchase is returned and a credit from the credit card company will be issued).

Installation
============

* No specific installation required.

Configuration
=============

* Go to Accounting > Configuration > Journals
* Create a new journal for your credit card
* Check the box ‘Transfer AP to Credit Card Company’ and set the ‘Credit Card Company’ field

Usage
=====

To use this module, you need to:

#. Go to Accounting > Purchases > Vendors Bills
#. Select an open bill and click on Register Payment
#. Select the credit card journal and validate the payment

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/96/10.0

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/account-payment/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smash it by providing detailed and welcomed feedback.

Credits
=======

Images
------

* Odoo Community Association: `Icon <https://github.com/OCA/maintainer-tools/blob/master/template/module/static/description/icon.svg>`_.

Contributors
------------

* Ray Carnes <rcarnes@ursainfosystems.com>
* Balaji Kannan <bkannan@ursainfosystems.com>
* Bhavesh Odedra <bodedra@ursainfosystems.com>
* Odoo Dev Team: DS, JA

Funders
-------

The development of this module has been financially supported by:

* Ursa Information Systems <http://www.ursainfosystems.com>

Maintainer
----------

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit https://odoo-community.org.
