.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=================================
Returned Customers Payment Orders
=================================

This module implements customer receivables returns and allows to send
related reconciled account move lines back to a state where the debt is still
open, and letting history of it.

This module can be extended adding importers that automatically fills the
full returned payment record.

Usage
=====

Go to Accounting > Customers > Customer Payment Returns, and create a new
record, register on each line a paid (reconciled) receivable journal item,
and input the amount that is going to be returned.

Another option to fill info is setting references and click match button to
find matches with invoices, move lines or moves. This functionality is extended
by other modules as *account_payment_return_import_sepa_pain*

It's possible to add a commission amount on each line.

Next, press button "Confirm" to create a new move line that removes the
balance from the bank journal and reconcile items together to show payment
history through it.

After confirmation you can access from the payment form view to the move
created.

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

Contributors
------------
* 7 i TRIA <http://www.7itria.cat>
* Avanzosc <http://www.avanzosc.com>
* Pedro M. Baeza <pedro.baeza@tecnativa.com>
* Markus Schneider <markus.schneider@initos.com>
* Sergio Teruel <sergio.teruel@tecnativa.com>
* Carlos Dauden <carlos.dauden@tecnativa.com>
* David Vidal <david.vidal@tecnativa.com>
* Luis M. Ontalba <luis.martinez@tecnativa.com>

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
