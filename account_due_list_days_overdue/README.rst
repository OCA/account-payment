.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=============================
Account Due List Days Overdue
=============================

This module adds to the 'Payments and due list' view the number of days that
 an open item is overdue, and classifies the amount due in separate terms
 columns  (e.g. 1-30, 31-60, +61).

The terms columns to show in the list and the number of days for within each
term can be configured.


Configuration
=============

* Go to 'Invoicing / Configuration / Overdue Terms', and add the terms,
  providing the day from, date to and a name that will be displayed in the
  Payments and due list as column.

* It is recommended to always add a last term '+ X' where the 'to days' value
  is a very big value like 99999.


Usage
=====

To use this module, you need to go to:

* Invoicing / Journal Entries / Payments and due list

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/96/8.0

Known issues / Roadmap
======================

No known issues.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/account-payment/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smashing it by providing a detailed and welcomed feedback.


Credits
=======

Contributors
------------

* Jordi Ballester Alomar <jordi.ballester@eficent.com>
* Holger Brunn <hbrunn@therp.nl>

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
