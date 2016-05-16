.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=========================================================
Migration scripts for account_payment_extension v7 module
=========================================================

This module includes the needed migration script for making a smooth transition
from v7 _account_payment_extension_ module to the set of v8 bank-payment
modules.

This module doesn't provide any functionality at user level.

Installation
============

You need openupgradelib for using these scripts, that can be installed via pip.
You need also to have accesible the repository bank-payment
from https://github.com/OCA/bank-payment.

Usage
=====

Update the modules and the conversion will be automatically done, and this
module will be automatically uninstalled.

Credits
=======

Contributors
------------

* Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>

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
