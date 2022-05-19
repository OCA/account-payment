# Copyright 2016 Cyril Gaudin (Camptocamp)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from psycopg2 import IntegrityError

from odoo.tests.common import TransactionCase
from odoo.tools.misc import mute_logger


class TestPaymentTerm(TransactionCase):

    @mute_logger('odoo.sql_db')
    def test_constraint__failed(self):
        # Logs are muted to prevent the expected integrity error from being
        # reported in the logs, which would cause a failed test status.
        with self.assertRaises(IntegrityError):
            self.env['account.payment.term'].create({
                'name': 'Unittest payment term',
                'early_payment_discount': True,
            })

    def test_constraint__good(self):
        payment_term = self.env['account.payment.term'].create({
            'name': 'Unittest payment term',
            'early_payment_discount': True,
            'epd_nb_days': 5,
            'epd_discount': 2
        })
        self.assertTrue(payment_term.early_payment_discount)

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

        self.assertFalse(payment_term.epd_nb_days)
        self.assertFalse(payment_term.epd_discount)
        self.assertFalse(payment_term.epd_tolerance)
