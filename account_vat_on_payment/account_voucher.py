# -*- coding: utf-8 -*-
# © 2011-2012 Domsense s.r.l. (<http://www.domsense.com>).
# © 2014 Agile Business Group sagl (<http://www.agilebg.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.osv import orm, fields
from openerp.tools.translate import _


class AccountVoucher(orm.Model):
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
                        line.move_line_id and line.move_line_id.invoice and
                        line.move_line_id.invoice.vat_on_payment
                    ):
                        vat_on_p += 1
            if vat_on_p and vat_on_p != valid_lines:
                raise orm.except_orm(
                    _('Error'),
                    _("Can't handle VAT on payment if not every invoice "
                      "is on a VAT on payment treatment"))
        return vat_on_p

    def _compute_allocated_amount(
        self, cr, uid, voucher, allocated=0, write_off=0, context=None
    ):
        allocated_amount = allocated + write_off
        if (
            voucher.exclude_write_off and
            voucher.payment_option == 'with_writeoff'
        ):
            # avoid including write-off if set in voucher.
            # That means: use the invoice's total
            # (as we are in 'full reconcile' case)
            allocated_amount = allocated
        return allocated_amount

    def _compute_new_line_amount(
        self, cr, uid, voucher, inv_move_line, amounts_by_invoice, invoice,
        context=None
    ):
        currency_obj = self.pool.get('res.currency')
        allocated_amount = self._compute_allocated_amount(
            cr, uid, voucher,
            allocated=amounts_by_invoice[invoice.id]['allocated'],
            write_off=amounts_by_invoice[invoice.id]['write-off'],
            context=context)
        # compute the VAT or base line proportionally to
        # the paid amount
        new_line_amount = currency_obj.round(
            cr, uid, voucher.company_id.currency_id,
            (allocated_amount / amounts_by_invoice[invoice.id]['total']) *
            (inv_move_line.credit or inv_move_line.debit)
        )
        return new_line_amount

    def _compute_new_line_currency_amount(
        self, cr, uid, voucher, inv_move_line, amounts_by_invoice, invoice,
        context=None
    ):
        currency_obj = self.pool.get('res.currency')
        new_line_amount_curr = False
        if (
            amounts_by_invoice[invoice.id].get('allocated_currency') and
            amounts_by_invoice[invoice.id].get('foreign_currency_id')
        ):
            for_curr = currency_obj.browse(
                cr, uid, amounts_by_invoice[invoice.id]['foreign_currency_id'],
                context=context)
            allocated_amount = self._compute_allocated_amount(
                cr, uid, voucher,
                allocated=amounts_by_invoice[invoice.id]['allocated_currency'],
                write_off=amounts_by_invoice[invoice.id]['currency-write-off'],
                context=context)
            new_line_amount_curr = currency_obj.round(
                cr, uid, for_curr,
                (
                    allocated_amount /
                    amounts_by_invoice[invoice.id]['total_currency']
                ) *
                (inv_move_line.amount_currency)
            )
        return new_line_amount_curr

    def _prepare_real_move_line(
        self, cr, uid, inv_move_line, new_line_amount, new_line_amount_curr,
        foreign_curr_id, context=None
    ):
        vat_config_error = inv_move_line.company_id.vat_config_error
        if not inv_move_line.real_account_id:
            if vat_config_error == 'raise_error':
                raise orm.except_orm(
                    _('Error'),
                    _("We are on a VAT on payment treatment "
                      "but move line %s does not have a related "
                      "real account")
                    % inv_move_line.name)
            else:
                real_account = inv_move_line.account_id.id
        else:
            real_account = inv_move_line.real_account_id.id
        # Add condition if having the same account, the debit and credit
        # should be 0 instead on increasing the turnover.
        if inv_move_line.account_id.id == inv_move_line.real_account_id.id:
            line_amount = 0.00
            line_amount_curr = 0.00
        else:
            line_amount = new_line_amount
            line_amount_curr = new_line_amount_curr
        vals = {
            'name': inv_move_line.name,
            'account_id': real_account,
            'credit': (inv_move_line.credit and line_amount or 0.0),
            'debit': (inv_move_line.debit and line_amount or 0.0),
            'type': 'real',
            'partner_id': (
                inv_move_line.partner_id and
                inv_move_line.partner_id.id or False)
        }
        if new_line_amount_curr and foreign_curr_id:
            vals['amount_currency'] = line_amount_curr
            vals['currency_id'] = foreign_curr_id
        if inv_move_line.tax_code_id:
            if not inv_move_line.real_tax_code_id:
                raise orm.except_orm(
                    _('Error'),
                    _("We are on a VAT on payment "
                      "treatment but move line %s does not "
                      "have a related real tax code")
                    % inv_move_line.name
                )
            vals['tax_code_id'] = inv_move_line.real_tax_code_id.id
            if inv_move_line.tax_amount < 0:
                vals['tax_amount'] = -new_line_amount
            else:
                vals['tax_amount'] = new_line_amount
        return vals

    def _prepare_shadow_move_line(
        self, cr, uid, inv_move_line, new_line_amount,
        context=None
    ):
        if inv_move_line.account_id.id == inv_move_line.real_account_id.id:
            line_amount = 0.00
        else:
            line_amount = new_line_amount
        vals = {
            'name': inv_move_line.name,
            'account_id': inv_move_line.account_id.id,
            'credit': (
                inv_move_line.debit and
                line_amount or 0.0),
            'debit': (
                inv_move_line.credit and
                line_amount or 0.0),
            'type': 'shadow',
            'partner_id': (
                inv_move_line.partner_id and
                inv_move_line.partner_id.id or False)
        }
        if inv_move_line.tax_code_id:
            vals[
                'tax_code_id'
            ] = inv_move_line.tax_code_id.id
            if inv_move_line.tax_amount < 0:
                vals['tax_amount'] = new_line_amount
            else:
                vals['tax_amount'] = -new_line_amount
        return vals

    def _prepare_shadow_move(
        self, cr, uid, document, move_id_field='move_id', context=None
    ):
        """
        document can be a voucher or a bank statement line, as they share
        almost every field, except move_id/journal_entry_id
        """
        vat_config_error = document.company_id.vat_config_error
        if not document.journal_id.vat_on_payment_related_journal_id:
            if vat_config_error == 'raise_error':
                raise orm.except_orm(
                    _('Error'),
                    _("We are on a VAT on payment treatment "
                      "but journal %s does not have a related shadow "
                      "journal")
                    % document.journal_id.name)
            else:
                real_journal = document.journal_id.id
        else:
            real_journal = (
                document.journal_id.vat_on_payment_related_journal_id.id)

        if move_id_field == 'move_id':
            move = document.move_id
        elif move_id_field == 'journal_entry_id':
            move = document.journal_entry_id
        return {
            'journal_id': real_journal,
            'period_id': move.period_id.id,
            'date': move.date,
        }

    def _move_payment_lines_to_shadow_entry(
        self, cr, uid, voucher, shadow_move_id, context=None
    ):
        for line in voucher.move_ids:
            if line.account_id.type != 'liquidity':
                # If the line is related to write-off and user doesn't
                # want to compute the tax including write-off,
                # write-off move line must stay on the real move
                if not (
                    voucher.exclude_write_off and
                    voucher.payment_option == 'with_writeoff' and
                    line.account_id.id ==
                    voucher.writeoff_acc_id.id
                ):
                    line.write({
                        'move_id': shadow_move_id,
                    }, update_check=False)
                # this will allow user to see the real entry from
                # invoice payment tab
                if (
                    line.account_id.type == 'receivable' or
                    line.account_id.type == 'payable'
                ):
                    line.write({
                        'real_payment_move_id': voucher.move_id.id,
                    })
        return True

    def _create_vat_on_payment_move(self, cr, uid, voucher, context=None):
        move_line_pool = self.pool.get('account.move.line')
        move_pool = self.pool.get('account.move')
        inv_pool = self.pool.get('account.invoice')
        vat_config_error = voucher.company_id.vat_config_error
        if not voucher.journal_id.vat_on_payment_related_journal_id:
            if vat_config_error == 'raise_error':
                raise orm.except_orm(
                    _('Error'),
                    _("We are on a VAT on payment treatment "
                      "but journal %s does not have a related shadow "
                      "journal")
                    % voucher.journal_id.name)
            else:
                real_journal = voucher.journal_id.id
        else:
            real_journal = (
                voucher.journal_id.vat_on_payment_related_journal_id.id)
        lines_to_create = []
        amounts_by_invoice = super(
            AccountVoucher, self
        ).allocated_amounts_grouped_by_invoice(
            cr, uid, voucher, context)
        for inv_id in amounts_by_invoice:
            invoice = inv_pool.browse(cr, uid, inv_id, context)
            for inv_move_line in invoice.move_id.line_id:
                if (
                    inv_move_line.account_id.type != 'receivable' and
                    inv_move_line.account_id.type != 'payable'
                ):
                    new_line_amount = self._compute_new_line_amount(
                        cr, uid, voucher, inv_move_line,
                        amounts_by_invoice, invoice, context=context)
                    new_line_amount_curr = (
                        self._compute_new_line_currency_amount(
                            cr, uid, voucher, inv_move_line,
                            amounts_by_invoice, invoice,
                            context=context)
                    )
                    foreign_currency_id = amounts_by_invoice[
                        invoice.id]['foreign_currency_id']
                    real_vals = self._prepare_real_move_line(
                        cr, uid, inv_move_line, new_line_amount,
                        new_line_amount_curr, foreign_currency_id,
                        context=context)
                    lines_to_create.append(real_vals)

                    shadow_vals = self._prepare_shadow_move_line(
                        cr, uid, inv_move_line, new_line_amount,
                        context=context)
                    lines_to_create.append(shadow_vals)

        ctx = dict(context) or {}
        ctx['journal_id'] = real_journal
        ctx['period_id'] = voucher.move_id.period_id.id
        shadow_move_id = move_pool.create(
            cr, uid, self._prepare_shadow_move(
                cr, uid, voucher, context=ctx), ctx)

        if voucher.company_id.vat_payment_lines == 'shadow_move':
            self._move_payment_lines_to_shadow_entry(
                cr, uid, voucher, shadow_move_id, context=ctx)

        for line_to_create in lines_to_create:
            line_to_create['move_id'] = shadow_move_id
            if (
                line_to_create['type'] == 'real' and
                voucher.company_id.vat_payment_lines == 'shadow_move'
            ):
                line_to_create['move_id'] = voucher.move_id.id
            del line_to_create['type']

            move_line_pool.create(cr, uid, line_to_create, ctx)

        voucher.write({'shadow_move_id': shadow_move_id})

        super(AccountVoucher, self).balance_move(
            cr, uid, shadow_move_id, ctx)
        super(AccountVoucher, self).balance_move(
            cr, uid, voucher.move_id.id, ctx)
        return True

    def action_move_line_create(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        journal_pool = self.pool.get('account.journal')
        res = False
        for voucher in self.browse(cr, uid, ids, context):
            entry_posted = voucher.journal_id.entry_posted
            # disable the 'skip draft state' option because "mixed" entry
            # (shadow + real) won't pass validation. Anyway every entry will be
            # posted later (if 'entry_posted' is enabled)
            if entry_posted:
                journal_pool.write(
                    cr, uid, voucher.journal_id.id, {'entry_posted': False})
            res = super(AccountVoucher, self).action_move_line_create(
                cr, uid, [voucher.id], context)
            # because 'move_id' has been updated by 'action_move_line_create'
            voucher.refresh()
            if self.is_vat_on_payment(voucher):
                self._create_vat_on_payment_move(
                    cr, uid, voucher, context=context)
            if entry_posted:
                journal_pool.write(
                    cr, uid, voucher.journal_id.id, {'entry_posted': True})
                voucher.move_id.post()
                if self.is_vat_on_payment(voucher):
                    voucher.shadow_move_id.post()

        return res

    def unreconcile_documents(
        self, cr, uid, ids, model='account.voucher', context=None
    ):
        """
        document can be voucher or bank statement line,
        as they share field names
        """
        reconcile_pool = self.pool.get('account.move.reconcile')
        move_pool = self.pool.get('account.move')
        for document in self.pool[model].browse(cr, uid, ids, context=context):
            recs = []
            if document.shadow_move_id:
                for line in document.shadow_move_id.line_id:
                    if line.reconcile_id:
                        recs += [line.reconcile_id.id]
                    if line.reconcile_partial_id:
                        recs += [line.reconcile_partial_id.id]

                reconcile_pool.unlink(cr, uid, recs)

                if document.shadow_move_id:
                    move_pool.button_cancel(
                        cr, uid, [document.shadow_move_id.id])
                    move_pool.unlink(cr, uid, [document.shadow_move_id.id])

    def cancel_voucher(self, cr, uid, ids, context=None):
        res = super(AccountVoucher, self).cancel_voucher(
            cr, uid, ids, context)
        self.unreconcile_documents(cr, uid, ids, context=context)
        return res
