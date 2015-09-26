.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=======================================
Paybox payment acquirer module for Odoo
=======================================

This module adds a new payment acquirer for your website sales: Paybox,
provided by Verifone.  Only useful for French organizations.

Installation
============

Requires the `Python Crypto module <http://www.pycrypto.org/>`_. Make sure to
run ``apt-get install python-crypto`` before installing this module.

Usage
=====

This modules installs with default values so that you can reach the Paybox
payment screen.  For proper tests, also install the ``website_sale`` module.  Go
to the Payment Acquirers configuration screen to set the return URL of your
Odoo installation to properly process the payment.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/account-payment/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/OCA/account-payment/issues/new?body=module:%20payment_paybox%0Aversion:%208.0.1.0.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Credits
=======

Contributors
------------

* Florent Jouatte, Anybox
* Jean-Baptiste Quenot

Maintainer
----------

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit http://odoo-community.org.
