.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

===============================
Account Cash Discount Write Off
===============================

Create an automatic write-off for payment with discount on the payment order
confirmation. If the cash discount amount is computed based on the total
amount, the created write-off will also contains tax adjustments. This
adjustments are computed based on the discount percent configured on the
related invoice.

Configuration
=============

To configure this module, you need to:

#. Go to your companies
#. Set the cash discount write off account
#. Set the cash discount write off journal

Usage
=====

To use this module, you need to:

#. Create a supplier invoice
#. In the "Other Info" tab, you can configure a discount in percent and a discount delay in days
#. Validate the invoice
#. Create a payment order and add the previously created invoice using the search based on the cash discount due date
#. Validate your payment order till the last state
#. The invoice is now marked as "Paid".

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/96/10.0

.. repo_id is available in https://github.com/OCA/maintainer-tools/blob/master/tools/repos_with_ids.txt
.. branch is "8.0" for example

Known issues / Roadmap
======================

* The cash discount should only be used when doing a full payment at once.

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

* Odoo Community Association: `Icon <https://github.com/OCA/maintainer-tools/blob/master/template/module/static/description/icon.png>`_.

Contributors
------------

* Benjamin Willig <benjamin.willig@acsone.eu>
* Christelle De Coninck (ACSONE) <christelle.deconinck@acsone.eu>

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
