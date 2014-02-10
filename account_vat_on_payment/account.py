# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011-2012 Domsense s.r.l. (<http://www.domsense.com>).
#    Copyright (C) 2012-2013 Agile Business Group sagl
#    (<http://www.agilebg.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import fields, osv
from tools.translate import _


class account_voucher(osv.osv):
    _inherit = "account.voucher"

    _columns = {
        'shadow_move_id': fields.many2one(
            'account.move', 'Shadow Entry', readonly=True),
        }

    def is_vat_on_payment(self, voucher):
        vat_on_p = 0
        valid_lines = 0
        if voucher.type in ('payment', 'receipt'):
            for line in voucher.line_ids:
                if line.amount:
                    valid_lines += 1
                    if (
                        line.move_line_id and line.move_line_id.invoice
                        and line.move_line_id.invoice.vat_on_payment
                    ):
                        vat_on_p += 1
            if vat_on_p and vat_on_p != valid_lines:
                raise osv.except_osv(
                    _('Error'),
                    _("""Can't handle VAT on payment if not every invoice
                    is on a VAT on payment treatment"""))
        return vat_on_p

    def action_move_line_create(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        inv_pool = self.pool.get('account.invoice')
        journal_pool = self.pool.get('account.journal')
        move_line_pool = self.pool.get('account.move.line')
        move_pool = self.pool.get('account.move')
        currency_obj = self.pool.get('res.currency')
        res = False
        for voucher in self.browse(cr, uid, ids, context):
            entry_posted = voucher.journal_id.entry_posted
            # disable the 'skip draft state' option because "mixed" entry
            # (shadow + real) won't pass validation. Anyway every entry will be
            # posted later (if 'entry_posted' is enabled)
            if entry_posted:
                journal_pool.write(
                    cr, uid, voucher.journal_id.id, {'entry_posted': False})
            res = super(account_voucher, self).action_move_line_create(
                cr, uid, [voucher.id], context)
            # because 'move_id' has been updated by 'action_move_line_create'
            voucher.refresh()
            if entry_posted:
                journal_pool.write(
                    cr, uid, voucher.journal_id.id, {'entry_posted': True})
            if self.is_vat_on_payment(voucher):
                if not voucher.journal_id.vat_on_payment_related_journal_id:
                    raise osv.except_osv(
                        _('Error'),
                        _("""We are on a VAT on payment treatment
                        but journal %s does not have a related shadow
                        journal""")
                        % voucher.journal_id.name)
                lines_to_create = []
                amounts_by_invoice = super(
                    account_voucher, self
                    ).allocated_amounts_grouped_by_invoice(
                    cr, uid, voucher, context)
                for inv_id in amounts_by_invoice:
                    invoice = inv_pool.browse(cr, uid, inv_id, context)
                    for inv_move_line in invoice.move_id.line_id:
                        if (
                            inv_move_line.account_id.type != 'receivable'
                            and inv_move_line.account_id.type != 'payable'
                        ):
                            # compute the VAT or base line proportionally to
                            # the paid amount
                            if (
                                voucher.exclude_write_off
                                and voucher.payment_option == 'with_writeoff'
                            ):
                                # avoid including write-off if set in voucher.
                                # That means: use the invoice's total
                                # (as we are in 'full reconcile' case)
                                allocated_amount = amounts_by_invoice[
                                    invoice.id
                                    ]['allocated']
                            else:
                                allocated_amount = (
                                    amounts_by_invoice[invoice.id]['allocated']
                                    +
                                    amounts_by_invoice[invoice.id]['write-off']
                                    )
                            new_line_amount = currency_obj.round(
                                cr, uid, voucher.company_id.currency_id,
                                (
                                    allocated_amount
                                    /
                                    amounts_by_invoice[invoice.id]['total']
                                )
                                *
                                (inv_move_line.credit or inv_move_line.debit)
                                )
                            new_line_amount_curr = False
                            if (
                                amounts_by_invoice[invoice.id].get(
                                    'allocated_currency')
                                and amounts_by_invoice[invoice.id].get(
                                    'foreign_currency_id')
                            ):
                                for_curr = currency_obj.browse(
                                    cr, uid,
                                    amounts_by_invoice[invoice.id][
                                        'foreign_currency_id'],
                                    context=context)
                                if (
                                    voucher.exclude_write_off
                                    and
                                    voucher.payment_option == 'with_writeoff'
                                ):
                                    # again
                                    # avoid including write-off if set in
                                    # voucher.
                                    allocated_amount = amounts_by_invoice[
                                        invoice.id]['allocated_currency']
                                else:
                                    allocated_amount = (
                                        amounts_by_invoice[invoice.id][
                                            'allocated_currency']
                                        +
                                        amounts_by_invoice[invoice.id][
                                            'currency-write-off']
                                        )
                                new_line_amount_curr = currency_obj.round(
                                    cr, uid, for_curr,
                                    (
                                        allocated_amount
                                        /
                                        amounts_by_invoice[
                                            invoice.id
                                        ]['total_currency']
                                    )
                                    *
                                    (inv_move_line.amount_currency)
                                    )

                            if not inv_move_line.real_account_id:
                                raise osv.except_osv(
                                    _('Error'),
                                    _("""We are on a VAT on payment treatment
                                    but move line %s does not have a related
                                    real account""")
                                    % inv_move_line.name)

                            # prepare the real move line
                            vals = {
                                'name': inv_move_line.name,
                                'account_id': inv_move_line.real_account_id.id,
                                'credit': (
                                    inv_move_line.credit
                                    and new_line_amount or 0.0),
                                'debit': (
                                    inv_move_line.debit
                                    and new_line_amount or 0.0),
                                'type': 'real',
                                'partner_id': (
                                    inv_move_line.partner_id
                                    and inv_move_line.partner_id.id or False)
                                }
                            if new_line_amount_curr:
                                vals['amount_currency'] = new_line_amount_curr
                                vals['currency_id'] = for_curr.id
                            if inv_move_line.tax_code_id:
                                if not inv_move_line.real_tax_code_id:
                                    raise osv.except_osv(
                                        _('Error'),
                                        _("""We are on a VAT on payment
                                        treatment but move line %s does not
                                        have a related real tax code""")
                                        % inv_move_line.name
                                    )
                                vals[
                                    'tax_code_id'
                                    ] = inv_move_line.real_tax_code_id.id
                                if inv_move_line.tax_amount < 0:
                                    vals['tax_amount'] = -new_line_amount
                                else:
                                    vals['tax_amount'] = new_line_amount
                            lines_to_create.append(vals)

                            # prepare the shadow move line
                            vals = {
                                'name': inv_move_line.name,
                                'account_id': inv_move_line.account_id.id,
                                'credit': (
                                    inv_move_line.debit
                                    and new_line_amount or 0.0),
                                'debit': (
                                    inv_move_line.credit
                                    and new_line_amount or 0.0),
                                'type': 'shadow',
                                'partner_id': (
                                    inv_move_line.partner_id
                                    and inv_move_line.partner_id.id or False)
                                }
                            if inv_move_line.tax_code_id:
                                vals[
                                    'tax_code_id'
                                    ] = inv_move_line.tax_code_id.id
                                if inv_move_line.tax_amount < 0:
                                    vals['tax_amount'] = new_line_amount
                                else:
                                    vals['tax_amount'] = -new_line_amount
                            lines_to_create.append(vals)

                context['journal_id'] = (
                    voucher.journal_id.vat_on_payment_related_journal_id.id)
                context['period_id'] = voucher.move_id.period_id.id
                shadow_move_id = move_pool.create(cr, uid, {
                    'journal_id': (
                        voucher.journal_id.vat_on_payment_related_journal_id.id
                        ),
                    'period_id': voucher.move_id.period_id.id,
                    'date': voucher.move_id.date,
                    }, context)

                # move the payment move lines to shadow entry
                for line in voucher.move_ids:
                    if line.account_id.type != 'liquidity':
                        # If the line is related to write-off and user doesn't
                        # want to compute the tax including write-off,
                        # write-off move line must stay on the real move
                        if not (
                            voucher.exclude_write_off
                            and voucher.payment_option == 'with_writeoff'
                            and line.account_id.id
                                == voucher.writeoff_acc_id.id
                        ):
                            line.write({
                                'move_id': shadow_move_id,
                                }, update_check=False)
                        # this will allow user to see the real entry from
                        # invoice payment tab
                        if (
                            line.account_id.type == 'receivable'
                            or line.account_id.type == 'payable'
                        ):
                            line.write({
                                'real_payment_move_id': voucher.move_id.id,
                                })

                for line_to_create in lines_to_create:
                    if line_to_create['type'] == 'real':
                        line_to_create['move_id'] = voucher.move_id.id
                    elif line_to_create['type'] == 'shadow':
                        line_to_create['move_id'] = shadow_move_id
                    del line_to_create['type']

                    move_line_pool.create(cr, uid, line_to_create, context)

                voucher.write({'shadow_move_id': shadow_move_id})

                super(account_voucher, self).balance_move(
                    cr, uid, shadow_move_id, context)
                super(account_voucher, self).balance_move(
                    cr, uid, voucher.move_id.id, context)

        return res

    def cancel_voucher(self, cr, uid, ids, context=None):
        res = super(account_voucher, self).cancel_voucher(
            cr, uid, ids, context)
        reconcile_pool = self.pool.get('account.move.reconcile')
        move_pool = self.pool.get('account.move')
        for voucher in self.browse(cr, uid, ids, context=context):
            recs = []
            if voucher.shadow_move_id:
                for line in voucher.shadow_move_id.line_id:
                    if line.reconcile_id:
                        recs += [line.reconcile_id.id]
                    if line.reconcile_partial_id:
                        recs += [line.reconcile_partial_id.id]

                reconcile_pool.unlink(cr, uid, recs)

                if voucher.shadow_move_id:
                    move_pool.button_cancel(
                        cr, uid, [voucher.shadow_move_id.id])
                    move_pool.unlink(cr, uid, [voucher.shadow_move_id.id])
        return res


class account_invoice(osv.osv):

    def _get_vat_on_payment(self, cr, uid, context=None):
        return self.pool.get('res.users').browse(
            cr, uid, uid, context).company_id.vat_on_payment

    def finalize_invoice_move_lines(self, cr, uid, invoice_browse, move_lines):
        """
        Use shadow accounts for journal entry to be generated, according to
        account and tax code related records
        """
        move_lines = super(account_invoice, self).finalize_invoice_move_lines(
            cr, uid, invoice_browse, move_lines)
        acc_pool = self.pool.get('account.account')
        tax_code_pool = self.pool.get('account.tax.code')
        new_move_lines = []
        for line_tup in move_lines:
            if invoice_browse.vat_on_payment:
                if line_tup[2].get('account_id', False):
                    account = acc_pool.browse(
                        cr, uid, line_tup[2]['account_id'])
                    if (
                        account.type != 'receivable'
                        and account.type != 'payable'
                    ):
                        if not account.vat_on_payment_related_account_id:
                            raise osv.except_osv(
                                _('Error'),
                                _('''The invoice is \'VAT on payment\' but
                                account %s does not have a related shadow
                                account''')
                                % account.name)
                        line_tup[2]['real_account_id'] = line_tup[
                            2]['account_id']
                        line_tup[2]['account_id'] = (
                            account.vat_on_payment_related_account_id.id)
                if line_tup[2].get('tax_code_id', False):
                    tax_code = tax_code_pool.browse(
                        cr, uid, line_tup[2]['tax_code_id'])
                    if not tax_code.vat_on_payment_related_tax_code_id:
                        raise osv.except_osv(
                            _('Error'),
                            _('''The invoice is \'VAT on payment\' but
                            tax code %s does not have a related shadow
                            tax code''')
                            % tax_code.name)
                    line_tup[2]['real_tax_code_id'] = line_tup[
                        2]['tax_code_id']
                    line_tup[2]['tax_code_id'] = (
                        tax_code.vat_on_payment_related_tax_code_id.id)
            new_move_lines.append(line_tup)
        return new_move_lines

    def onchange_partner_id(self, cr, uid, ids, type, partner_id,\
            date_invoice=False, payment_term=False, partner_bank_id=False, company_id=False):
        res = super(account_invoice, self).onchange_partner_id(cr, uid, ids, type, partner_id, date_invoice, payment_term, partner_bank_id, company_id)
        # default value for VAT on Payment is changed every time the customer/supplier is changed
        partner_obj = self.pool.get("res.partner")
        for partner_id in partner_obj.browse(cr, uid, [partner_id]):
            res['value']['vat_on_payment'] = True if partner_id.default_has_vat_on_payment == 'true' else False
        return res

    _inherit = "account.invoice"
    _columns = {
        'vat_on_payment': fields.boolean('Vat on payment'),
        }
    _defaults = {
        'vat_on_payment': _get_vat_on_payment,
        }


class account_move_line(osv.osv):
    _inherit = "account.move.line"
    _columns = {
        'real_payment_move_id': fields.many2one(
            'account.move', 'Real payment entry'),
        'real_account_id': fields.many2one('account.account', 'Real account'),
        'real_tax_code_id': fields.many2one(
            'account.tax.code', 'Real tax code'),
        }


class account_account(osv.osv):
    _inherit = "account.account"
    _columns = {
        'vat_on_payment_related_account_id': fields.many2one(
            'account.account', 'Shadow Account for VAT on payment',
            help='''Related account used for real registrations on a
            VAT on payment basis. Set the shadow account here'''),
        }


class account_tax_code(osv.osv):
    _inherit = "account.tax.code"
    _columns = {
        'vat_on_payment_related_tax_code_id': fields.many2one(
            'account.tax.code', 'Shadow Tax code for VAT on payment',
            help='''Related tax code used for real registrations on a
            VAT on payment basis. Set the shadow tax code here'''),
        }


class account_journal(osv.osv):
    _inherit = "account.journal"
    _columns = {
        'vat_on_payment_related_journal_id': fields.many2one(
            'account.journal', 'Shadow Journal for VAT on payment',
            help='''Related journal used for shadow registrations on a
            VAT on payment basis. Set the shadow journal here'''),
        }
