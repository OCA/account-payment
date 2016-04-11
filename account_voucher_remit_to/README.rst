Account voucher remit-to address
================================
This module aims to introduce the possibility to assign a remit-to address
to a partner, that is then used at the time of printing a voucher.

The remit-to address is typically used related to the preparation of checks.


Installation
============

No additional installation instructions are required.


Configuration
=============

This module does not require any additional configuration.

Usage
=====

The user can create a partner with address type 'Remit-to'.

When the user creates a voucher for a partner, if this partner has a related
partner with address type 'Remit-to', it will be proposed.

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/154/7.0


Known issues / Roadmap
======================

The address type field is redefined in this module to add the new type
'remit-to'. Extension of selection fields is a problem in v7, because any
other module that also extends this field will cause the extended address
type to disappear.


Credits
=======

Contributors
------------

* Jordi Ballester <jordi.ballester@eficent.com>

Maintainer
----------

.. image:: http://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: http://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit http://odoo-community.org.