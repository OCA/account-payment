.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

==================================
Supply res.currency.print_on_check
==================================

This module improves res.currency by adding the "print_on_check" field, which
stores the human readable name of the currency (US Dollar, Euro, Canadian
Dollar, etc.)

* English names for currencies can be found in https://en.wikipedia.org/wiki/ISO_4217
* Spanish translations were taken from https://es.wikipedia.org/wiki/ISO_4217

Please, feel free to include any translations that it may be missing.

Installation
============

To install this module, just select it from available modules.

Configuration
=============

This module has pre loaded names that you can use to print currencies names,
the only configuration you can do is set translations names for every currency
you use in your Odoo.

Usage
=====

The use this module you need to include the field `field_on_check` in your 
reports for your payments, invoices, POS tickets, etc.

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/96/9.0

Known issues / Roadmap
======================

* No issues reported yet

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/account-payment/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smashing it by providing a detailed and welcomed feedback.

Credits
=======

Images
------

* Odoo Community Association: `Icon <https://github.com/OCA/maintainer-tools/blob/master/template/module/static/description/icon.svg>`_.

Contributors
------------

* Joao Alfredo Gama Batista <joao.gama@savoirfairelinux.com>
* Virgil Dupras <virgil.dupras@savoirfairelinux.com>
* Sandy Carter <sandy.carter@savoirfairelinux.com>
* Primaco <info@primaco.ca>
* Osval Reyes <osval@vauxoo.com>

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
