# Copyright 2012 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime, timedelta
from odoo.tests import common
from odoo import fields
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class TestPartnerAging(common.TransactionCase):

    def setUp(self):
        super(TestPartnerAging, self).setUp()
        self.partner_aging_date_model = self.env['res.partner.aging.date']
        self.partner_aging_supplier_model =\
            self.env['res.partner.aging.supplier']
        self.partner_aging_customer_model =\
            self.env['res.partner.aging.customer']
        self.current_date = fields.Date.today()
        self.account_invoice_obj = self.env['account.invoice']
        self.payment_term = self.env.ref(
            'account.account_payment_term_advance')
        self.journalrec = \
            self.env['account.journal'].search([('type', '=', 'sale')])[0]
        self.partner_12 = self.env.ref('base.res_partner_12')
        self.partner_2 = self.env.ref('base.res_partner_2')
        self.partner_10 = self.env.ref('base.res_partner_10')
        self.partner_3 = self.env.ref('base.res_partner_3')
        self.partner_18 = self.env.ref('base.res_partner_18')
        invoice_line_data = [
            (0, 0,
             {'product_id': self.env.ref('product.product_product_5').id,
              'quantity': 10.0,
              'account_id': self.env['account.account'].search(
                  [('user_type_id', '=', self.env.ref(
                      'account.data_account_type_revenue').id)],
                  limit=1).id,
              'name': 'product test 5',
              'price_unit': 100.00})]
        self.account_invoice_customer0 = self.account_invoice_obj.create(dict(
            name="Test Customer Invoice",
            payment_term_id=self.payment_term.id,
            journal_id=self.journalrec.id,
            partner_id=self.partner_12.id,
            invoice_line_ids=invoice_line_data,
            date_invoice=self.get_date(30),
            date_due=self.get_date(30),
            type='out_invoice'))
        self.account_invoice_customer1 = self.account_invoice_customer0.copy(
            dict(date_invoice=self.get_date(60),
                 date_due=self.get_date(60),
                 partner_id=self.partner_2.id))
        self.account_invoice_customer2 = self.account_invoice_customer0.copy(
            dict(date_invoice=self.get_date(90),
                 date_due=self.get_date(90),
                 partner_id=self.partner_18.id))
        self.account_invoice_customer3 = self.account_invoice_customer0.copy(
            dict(date_invoice=self.get_date(119),
                 date_due=self.get_date(119),
                 partner_id=self.partner_3.id))
        self.account_invoice_customer4 = self.account_invoice_customer0.copy(
            dict(date_invoice=self.get_date(124),
                 date_due=self.get_date(124),
                 partner_id=self.partner_10.id))
        self.account_invoice_customer0.action_invoice_open()
        self.account_invoice_customer1.action_invoice_open()
        self.account_invoice_customer2.action_invoice_open()
        self.account_invoice_customer3.action_invoice_open()
        self.account_invoice_customer4.action_invoice_open()
        self.account_invoice_supplier0 = self.account_invoice_obj.create(dict(
            name="Test Supplier Invoice",
            payment_term_id=self.payment_term.id,
            journal_id=self.journalrec.id,
            partner_id=self.partner_3.id,
            invoice_line_ids=invoice_line_data,
            date_invoice=self.get_date(30),
            date_due=self.get_date(30),
            type='in_invoice'))
        self.account_invoice_supplier1 = self.account_invoice_supplier0.copy(
            dict(date_invoice=self.get_date(60),
                 date_due=self.get_date(60)))
        self.account_invoice_supplier2 = self.account_invoice_supplier0.copy(
            dict(date_invoice=self.get_date(90),
                 date_due=self.get_date(90)))
        self.account_invoice_supplier3 = self.account_invoice_supplier0.copy(
            dict(date_invoice=self.get_date(119),
                 date_due=self.get_date(119)))
        self.account_invoice_supplier4 = self.account_invoice_supplier0.copy(
            dict(date_invoice=self.get_date(124),
                 date_due=self.get_date(124)))
        self.account_invoice_supplier0.action_invoice_open()
        self.account_invoice_supplier1.action_invoice_open()
        self.account_invoice_supplier2.action_invoice_open()
        self.account_invoice_supplier3.action_invoice_open()
        self.account_invoice_supplier4.action_invoice_open()

    def get_date(self, set_days):
        return (datetime.now() - timedelta(
            days=-set_days)).strftime(DEFAULT_SERVER_DATE_FORMAT)

    def test_partner_aging_customer(self):
        partner_aging_date = self.partner_aging_date_model.create(
            {'age_date': self.current_date})
        res = partner_aging_date.open_customer_aging()
        self.assertEqual(res['context']['age_date'], self.current_date)
        partner_aging_customer_rec = self.partner_aging_customer_model.search([
            ('invoice_id', '!=', False)], limit=1)
        partner_aging_customer_rec.open_document()

    def test_partner_aging_supplier(self):
        partner_aging_date = self.partner_aging_date_model.create(
            {'age_date': self.current_date})
        res = partner_aging_date.open_supplier_aging()
        self.assertEqual(res['context']['age_date'], self.current_date)
        partner_aging_supplier_rec = self.partner_aging_supplier_model.search([
            ('invoice_id', '!=', False)], limit=1)
        partner_aging_supplier_rec.open_document()
