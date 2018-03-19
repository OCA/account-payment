.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

=============================
Account Due List Payment Mode
=============================

This module adds a field to the due list of pending payments:

* the *Payment Mode* of invoices on account move lines.

Installation
============

This module depends on:

* account_due_list
* account_payment_partner

Configuration
=============

In order to see payments, you must install account_invoicing app, and you need
to check "Show full accounting features" in user permission.

Usage
=====

#. Go to *Invoicing > Adviser > Payments and due list* and you'll see the new
   field payment mode in the due list.

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/96/11.0


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

* Obertix Free Solutions <http://obertix.net>
* Sergio Teruel <sergio.teruel@tecnativa.com>
* Albert De La Fuente <info@haevas.com>
* Vicent Cubells <vicent.cubells@tecnativa.com>

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
