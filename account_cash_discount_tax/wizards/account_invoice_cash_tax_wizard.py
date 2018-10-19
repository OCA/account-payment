# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountInvoiceCashTaxWizard(models.TransientModel):

    _name = 'account.invoice.cash.tax.wizard'

    name = fields.Char()
    invoice_id = fields.Many2one(
        'account.invoice',
        ondelete='cascade',
        required=True,
    )
    description = fields.Char(
        related='invoice_id.company_id.cash_discount_tax_description',
        readonly=True,
    )
    account_id = fields.Many2one(
        'account.account',
        related='invoice_id.company_id.cash_discount_tax_account_id',
        readonly=True,
    )

    @api.model
    def default_get(self, fields_list):
        res = super(AccountInvoiceCashTaxWizard, self).default_get(
            fields_list)
        active_id = self.env.context.get('active_id')
        if active_id and \
                self.env.context.get('active_model') == 'account.invoice':
            res.update({
                'invoice_id': active_id,
            })
        return res

    @api.multi
    def _clean_invoice(self):
        """
        Remove former cash discount lines for taxes (in memory for
        performances)
        :return:
        """
        self.ensure_one()
        self.invoice_id.invoice_line_ids.filtered(
            'is_cash_discount_tax').unlink()

    @api.multi
    def _get_invoice_taxes(self, lines):
        """
        Parse invoice resultant taxes
        :param lines:
        :return:
        """
        for invoice_tax in self.invoice_id.tax_line_ids:
            # Create one line without tax
            amount = invoice_tax.base *\
                (self.invoice_id.discount_percent / 100)
            line_add = {
                'name': self.description,
                'price_unit': amount,
                'account_id': self.account_id.id,
                'quantity': 1.0,
                'is_cash_discount_tax': True,
            }
            line_rem = {
                'name': self.description,
                'price_unit': amount,
                'account_id': self.account_id.id,
                'quantity': -1.0,
                'is_cash_discount_tax': True,
                'invoice_line_tax_ids': [(6, 0, [invoice_tax.tax_id.id])],
            }
            lines.append((0, 0, line_add), )
            lines.append((0, 0, line_rem))

    @api.multi
    def _get_invoice_lines_taxes(self, lines):
        """
        Parse invoice line taxes
        :param lines:
        :return:
        """
        taxes = self.invoice_id.invoice_line_ids.mapped('invoice_line_tax_ids')
        amount_per_base_tax = {}
        for line in self.invoice_id.invoice_line_ids:
            for line_tax in line.invoice_line_tax_ids:
                current = amount_per_base_tax.get(line_tax.id)
                amount = (current + line.price_subtotal) if current else\
                    line.price_subtotal
                amount_per_base_tax.update({
                    line_tax.id: amount
                })
        for tax in taxes:
            amount = amount_per_base_tax.get(tax.id) *\
                (self.invoice_id.discount_percent / 100)
            line_add = {
                'name': self.description,
                'price_unit': amount,
                'account_id': self.account_id.id,
                'quantity': 1.0,
                'is_cash_discount_tax': True,
            }
            line_rem = {
                'name': self.description,
                'price_unit': amount,
                'account_id': self.account_id.id,
                'quantity': -1.0,
                'is_cash_discount_tax': True,
                'invoice_line_tax_ids': [(6, 0, [tax.id])],
            }
            lines.append((0, 0, line_add), )
            lines.append((0, 0, line_rem))

    @api.multi
    def _prepare_invoice_lines(self):
        """
        We parse all taxes through line taxes (invoice_id.tax_line_ids could
        have been generated through a tax group - but we don't want individual
        ones)
        :return: list
        """
        self.ensure_one()
        invoice_taxes = self.invoice_id.company_id.cash_discount_invoice_tax
        lines = []
        if invoice_taxes:
            self._get_invoice_taxes(lines)
        else:
            self._get_invoice_lines_taxes(lines)
        return lines

    @api.multi
    def doit(self):
        for wizard in self:
            wizard._clean_invoice()
            lines = wizard._prepare_invoice_lines()
            wizard.invoice_id.write({
                'invoice_line_ids': lines
            })
            wizard.invoice_id.compute_taxes()
        return True
