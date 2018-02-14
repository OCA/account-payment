# -*- coding: utf-8 -*-
# Copyright 2016 Eficent Business and IT Consulting Services S.L.
# (http://www.eficent.com)
# Copyright 2016 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models, api


class AccountRegisterPayments(models.TransientModel):
    _inherit = "account.register.payments"

    @api.multi
    def create_payment(self):
        res = super(AccountRegisterPayments, self).create_payment()
        if (self.journal_id.check_print_auto and
                self.payment_method_id.code == 'check_printing'):
            payment = self.env['account.payment'].search([
                ('journal_id', '=', self.journal_id.id),
                ('payment_method_id.name', 'like',
                 self.payment_method_id.name)], order="id desc", limit=1)
            return payment.do_print_checks()
        return res


class AccountPayment(models.Model):
    _inherit = "account.payment"

    @api.multi
    def do_print_checks(self):
        for rec in self:
            if rec.company_id.check_layout_id:
                return self.env['report'].get_action(
                    rec, rec.company_id.check_layout_id.report)
            return super(AccountPayment, self).do_print_checks()

    @api.multi
    def post(self):
        res = super(AccountPayment, self).post()
        if (self.journal_id.check_print_auto and
                self.payment_method_id.code == 'check_printing'):
            return self.do_print_checks()
        return res
