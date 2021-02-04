.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=======================
OSI Custom Payment Term
=======================

This module allows to set special discount for customer within periods of
discount days.

Configuration
=============

* Go to Accounting > Configuration > Management > Payment Terms
* Create payment terms. Make sure the is cash discount box is checked.
* Add landed costs by selecting the landed cost product and entering the
  percentage
* Add terms lines and provide discount percentage, discount days, expense and
  income account.

Usage
=====

* Create customer invoice and validate it.
* Apply register payment and set payment date which come eariler to discount
  days. For example: customer invoice amount is $1,000 and special discount(5%)
  available if payment done within 10 days. If customer will pay within 10 days,
  then register payment amount will be $950. System will make it as paid
  invoice. Because $50 is 5% discount of $1000 (customer invoice total amount.)
  If customer will pay $900 then invoice will be stay in open state. Because
  $100 is greater than of $50.

Credits
=======

ChriCar Beteiligungs- und Beratungs- GmbH (<http://www.camptocamp.at>)
Opensource Integrators (https://www.opensourceintegrators.com)

Contributors
------------

* Bhavesh Odedra <bodedra@opensourceintegrators.com>
* Balaji Kannan <bkannan@opensourceintegrators.com>
* Raphael Lee <rlee@opensourceintegrators.com>
* Hardik Suthar <hsuthar@opensourceintegrators.com>
