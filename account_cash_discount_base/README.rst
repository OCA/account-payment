.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :alt: License: AGPL-3

==========================
Account Cash Discount Base
==========================

This module was written to allow you to define cash discount (aka early payment discount)
on customer or supplier invoices.

On customer invoices, you can add a discount delay and
a discount percentage. At invoice validation, the discount due date is generated
from the delay. The amount with discount deducted is computed at the same time
as taxes. This module also adds cash discount informations on customer invoice
report.

On supplier invoices, you can set the discount percentage. For the discount due
date, you can fill it directly or set a delay. In this case, discount due date
is still computed at invoice's validation.

You can decide to calculate the discount amount based on the total price taxes
included or not.


Configuration
=============

To configure the base amount type, you need to:

#. Go to your companies
#. Set the cash discount base amount type (including taxes or not)

You can also configure default discount percent and delay on the payment term.


Usage
=====

To use this module you can defined all of informations written in the
description on customer and supplier invoices.

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/96/10.0

For further information, please visit:

 * https://www.odoo.com/forum/help-1

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/account-payment/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/OCA/account-payment/issues/new?body=module:%20account_cash_discount_base%0Aversion:%208.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Credits
=======

Contributors:
-------------

* Christelle De Coninck (ACSONE) <christelle.deconinck@acsone.eu>
* Stéphane Bidoul (ACSONE) <stephane.bidoul@acsone.eu>
* Adrien Peiffer (ACSONE) <adrien.peiffer@acsone.eu>
* Benjamin Willig (ACSONE) <benjamin.willig@acsone.eu>

Maintainer:
-----------

.. image:: http://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: http://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose mission is to support the collaborative development of Odoo features and promote its widespread use.

To contribute to this module, please visit http://odoo-community.org.
