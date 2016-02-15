.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

VAT on payment
==============

This module add VAT on payment behaviour on company configuration.

Modules depends on account_voucher_cash_basis, so check out the 
module 'account_voucher_cash_basis' description also.

Usage
=====

In Settings -> Accounting you have a new group called VAT on Payment.

From this you can set:

* If the company applies VAT on Payment, by checking the "VAT on payment treatment" boolean field.
* You can set if you want to move the payment line to the Shadow Move from the "VAT lines on Payment" selection field, if you choose "Keep on Real Move" option, this will not change the implicit move generated on payment, it will add all extra moves to the Shadow move
* From the selection field "Missconfiguration on VAT on Payment" you can choose if will raise an error if you missconfigured one account or journal, and use the same one. This behaviour is only available if you are not moving the payment lines to Shadow Entry.

By default you have to configure on tax code object, Related tax code used for real registrations on a VAT on payment basis.

Depending on the selection field from the configuration, you can configure:

* On account object, Related account used for real registrations on a VAT on payment basis
* On journal object, Related journal used for shadow registrations on a VAT on payment basis

Requirements: http://goo.gl/Nu0wDf

How to: http://planet.agilebg.com/en/2012/10/vat-on-payment-treatment-with-openerp/

Also, see demo and test data.

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/96/8.0

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/account-payment/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/OCA/account-payment/issues/new?body=module:%20account_vat_on_payment%0Aversion:%208.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Credits
=======

Contributors
------------

* Lorenzo Battistini <lorenzo.battistini@agilebg.com>
* Alex Comba <alex.comba@agilebg.com>
* Leonardo Pistone <lpistone@gmail.com>
* Fekete Mihai <feketemihai@gmail.com>

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
