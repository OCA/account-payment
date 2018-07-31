# -*- coding: utf-8 -*-
# Copyright (C) 2012 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.tests.common import TransactionCase
from openerp import fields


class TestPartnerAging(TransactionCase):

    def test_partner_aging_date(self):
        current_date = fields.Datetime.now()
        partner_aging_date = self.env['res.partner.aging.date'].create(
            {'age_date': current_date})
        partner_aging_date.age_date = current_date
        # call function open_customer_aging here
        res = partner_aging_date.open_customer_aging()
        self.assertEqual(res['context']['age_date'], current_date)

        # call open_supplier_aging and update current_date for good measure
        current_date = fields.Datetime.now()
        partner_aging_date.age_date = current_date
        res = partner_aging_date.open_supplier_aging()
        self.assertEqual(res['context']['age_date'], current_date)
