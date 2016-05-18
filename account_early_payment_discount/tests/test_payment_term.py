# -*- coding: utf-8 -*-
# © 2016 Cyril Gaudin (Camptocamp)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from psycopg2 import IntegrityError

from openerp.tests.common import TransactionCase


class TestPaymentTerm(TransactionCase):

    def test_constraint__failed(self):
        with self.assertRaises(IntegrityError):
            self.env['account.payment.term'].create({
                'name': 'Unittest payment term',
                'early_payment_discount': True,
            })

    def test_constraint__good(self):
        self.env['account.payment.term'].create({
            'name': 'Unittest payment term',
            'early_payment_discount': True,
            'epd_nb_days': 5,
            'epd_discount': 2
        })

    def test_onchange_early_payment_discount(self):
        payment_term = self.env['account.payment.term'].create({
            'name': 'Unittest payment term',
            'early_payment_discount': True,
            'epd_nb_days': 5,
            'epd_discount': 2,
            'epd_tolerance': 0.05,
        })

        payment_term.early_payment_discount = False
        payment_term._onchange_early_payment_discount()

        self.assertEqual(False, payment_term.epd_nb_days)
        self.assertEqual(False, payment_term.epd_discount)
        self.assertEqual(False, payment_term.epd_tolerance)
