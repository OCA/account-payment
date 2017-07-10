.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=============================
Account Payment Return Import
=============================

This module adds a generic wizard + methods to import payment return file
formats.

It's a base to be extended by another modules though it allows to import a csv
that will proccess the return payments on it.

Multiple payment return files contained in a zip are also supported.

Usage
=====

Under *Invoicing > Sales* there is available a new menu called *Import Payment
Return* that drives to a wizard that allows to upload a csv with that has to
have the following columns (* for required):

::

   account_number
   name *
   date *
   amount *
   unique_import_id *
   concept
   reason_code
   reason
   partner_name
   reference

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/96/10.0

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

* Carlos Dauden <pedro.baeza@tecnativa.com>
* Pedro M. Baeza <pedro.baeza@tecnativa.com>
* David Vidal <david.vidal@tecnativa.com>

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
