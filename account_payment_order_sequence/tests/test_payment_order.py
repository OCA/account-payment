# -*- coding: utf-8 -*-
# Copyright 2016 OpenSynergy Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.tests.common import TransactionCase


class PaymentOrderCase(TransactionCase):

    def setUp(self, *args, **kwargs):
        super(PaymentOrderCase, self).setUp(*args, **kwargs)

        obj_sequence = self.env["ir.sequence"]
        self.obj_order = self.env["payment.order"]

        sequence1 = obj_sequence.create({
            "name": "X sequence 1",
            "prefix": "01-",
            "padding": 0,
        })

        sequence2 = obj_sequence.create({
            "name": "X sequence 1",
            "prefix": "02-",
            "padding": 0,
        })

        self.mode1 = self.env.ref(
            "account_payment.payment_mode_1").copy(
                default={
                    "name": "X Mode 1",
                    "sequence_id": sequence1.id,
                })
        self.mode2 = self.env.ref(
            "account_payment.payment_mode_1").copy(
                default={
                    "name": "X Mode 1",
                    "sequence_id": sequence2.id,
                })

        self.mode3 = self.env.ref(
            "account_payment.payment_mode_1").copy(
                default={
                    "name": "X Mode 3",
                })

    def test_1(self):
        order1 = self._prepare_order(
            self.mode1.id)
        self.assertEqual(
            order1.reference,
            "01-1")
        order2 = self._prepare_order(
            self.mode2.id)
        self.assertEqual(
            order2.reference,
            "02-1")
        self._prepare_order(
            self.mode3.id)
        order4 = order2.copy()
        self.assertEqual(
            order4.reference,
            "02-2")

    def _prepare_order(self, mode):
        return self.obj_order.create({
            "mode": mode,
        })
