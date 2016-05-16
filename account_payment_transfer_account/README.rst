.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

Account Payment - Custom Transfer Account
=========================================

This module was written to extend the functionality of odoo Account payment
about transfer account.

.. image:: /account_payment/static/description/account_payment.png

With this module, it is now allowed to define for each internal transfer in
an account payment, a specific transfer account instead of the default one set
in 'Invoicing' / 'Configuration' / 'Setting' Section.
("Inter-Banks Transfer Account" field)

.. image:: /account_payment_transfer_account/static/description/account_payment.png

Note
====

Because Odoo Core is not overloadable (transfer account is hard coded in the
whole apps), This module will generate entries and after cancel entries to
set correct account, and after post again entries.

For that reason, this module depends on 'account_cancel' module.

Installation
============

Normal installation.

Configuration
=============

* Edit your accounts you want to use to make internal payment
.. image:: /account_payment_transfer_account/static/description/account_account.png

Usage
=====

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/96/9.0

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/{project_repo}/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smashing it by providing a detailed and welcomed feedback.

Credits
=======

Images
------

* Odoo Community Association: `Icon <https://github.com/OCA/maintainer-tools/blob/master/template/module/static/description/icon.svg>`_.

Contributors
------------

* Sylvain LE GAL <https://twitter.com/legalsylvain>

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
