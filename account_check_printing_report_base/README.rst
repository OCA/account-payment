.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

==================================
Account Check Printing Report Base
==================================

This module provides the basic framework for check printing, and a sample
layout.

Installation
============

In order to install this module you must first install also the module
'report_paper_wkhtmltopdf_params', available in
https://github.com/OCA/server-tools

Configuration
=============

Go to 'Settings / Users / Companies' and assign the desired check format.
This module proposes a basic layout, but other modules such as
"account_check_printing_report_dlt103" provide formats adjusted to known
check formats such as DLT103.

Usage
=====

* Go to 'Invoicing / Purchases / Payments'. Select one of the payments with
  type 'Check' and print the check.
* For automatic check printing when validating payment, mark the field in
  the journal associated.

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/96/11.0

Known issues / Roadmap
======================

* When print check automatically in the payment validation process, the wizard
  remains opened.

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

* Jordi Ballester Alomar <jordi.ballester@eficent.com>
* Lois Rilo Antelo <lois.rilo@eficent.com>
* Sandip Mangukiya <smangukiya@ursainfosystems.com>
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
