.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3


Payment order
============================

This module brings back the payment.order from v8.

This module also provide an infrastructure to export payment orders.
It includes some bug fixes and obvious enhancements to payment orders that will hopefully land in offical addons one
day.
This technical module provides the base infrastructure to export payment orders
for electronic banking. It provides the following technical features:

* a new payment.mode.type model
* payment.mode now has a mandatory type
* the "make payment" button launches a wizard depending on the
  payment.mode.type
* a manual payment mode type is provided as an example, with a default "do
  nothing" wizard
  
To enable the use of payment order to collect money for customers,
it adds a payment_order_type (payment|debit) as a basis of direct debit support
(this field becomes visible when account_direct_debit is installed).


Installation
============

This module depends on:

* base_iban

This modules is part of the OCA/account-payment suite.


Usage
=====

This module provides a menu to configure payment order types : Accounting > Configuration > Miscellaneous > Payment Export Types 

For further information, please visit:

 * https://www.odoo.com/forum/help-1

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/125/9.0


Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/l10n-switzerland/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/OCA/l10n-switzerland/issues/new?body=module:%20l10n_ch_states%0Aversion:%208.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.


Credits
=======

Contributors
------------
* Nicolas Bessi. Copyright Camptocamp SA
* Miguel Tallón, brain-tec AG
* Kumar Aberer, brain-tec AG
* Stéphane Bidoul <stephane.bidoul@acsone.eu>
* Alexis de Lattre		
* Pedro M. Baeza     
* Adrien Peiffer <adrien.peiffer@acsone.eu>
* Stefan Rijnhart
* Laurent Mignon <laurent.mignon@acsone.eu>
* Alexandre Fayolle
* Danimar Ribeiro
* Erwin van der Ploeg
* Raphaël Valyi
* Sandy Carter
* Angel Moya <angel.moya@domatix.com>


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
