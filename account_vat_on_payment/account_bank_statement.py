# -*- coding: utf-8 -*-
# © 2011-2012 Domsense s.r.l. (<http://www.domsense.com>).
# © 2014 Agile Business Group sagl (<http://www.agilebg.com>)
# © 2015 Forest and Biomass Services Romania (<https://www.forbiom.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.osv import orm, fields
from openerp.tools.translate import _
import copy


class AccountBankStatementLine(orm.Model):
    _inherit = "account.bank.statement.line"

    _columns = {
        'shadow_move_id': fields.many2one(
            'account.move', 'Shadow Entry', readonly=True),
    }

    def is_vat_on_payment(self, cr, uid, mv_line_dicts):
        move_line_pool = self.pool.get('account.move.line')
        vat_on_p = 0
        valid_lines = 0
        for mv_line_dict in mv_line_dicts:
            if (
                mv_line_dict.get('is_tax_line') or not
                mv_line_dict.get('counterpart_move_line_id')
            ):
                continue
            valid_lines += 1
            mv_line = move_line_pool.browse(
                cr, uid, mv_line_dict['counterpart_move_line_id'])
            invoice = mv_line.invoice
            if invoice.vat_on_payment:
                vat_on_p += 1
        if vat_on_p and vat_on_p != valid_lines:
            raise orm.except_orm(
                _('Error'),
                _("Can't handle VAT on payment if not every invoice "
                  "is on a VAT on payment treatment"))
        return vat_on_p

    def _compute_new_line_amount(
        self, cr, uid, bank_line, inv_move_line, amounts_by_invoice, invoice,
        context=None
    ):
        currency_obj = self.pool.get('res.currency')
        allocated_amount = (
            amounts_by_invoice[invoice.id]['allocated'] +
            amounts_by_invoice[invoice.id]['write-off']
        )
        # compute the VAT or base line proportionally to
        # the paid amount
        new_line_amount = currency_obj.round(
            cr, uid, bank_line.company_id.currency_id,
            (allocated_amount / amounts_by_invoice[invoice.id]['total']) *
            (inv_move_line.credit or inv_move_line.debit)
        )
        return new_line_amount

    def _compute_new_line_currency_amount(
        self, cr, uid, inv_move_line, amounts_by_invoice, invoice,
        context=None
    ):
        currency_obj = self.pool.get('res.currency')
        new_line_amount_curr = False
        if (amounts_by_invoice[invoice.id].get('allocated_currency') and
                amounts_by_invoice[invoice.id].get('foreign_currency_id')):
            for_curr = currency_obj.browse(
                cr, uid, amounts_by_invoice[invoice.id]['foreign_currency_id'],
                context=context)
            allocated_amount = (
                amounts_by_invoice[invoice.id]['allocated_currency'] +
                amounts_by_invoice[invoice.id]['currency-write-off']
            )
            new_line_amount_curr = currency_obj.round(
                cr, uid, for_curr,
                (allocated_amount /
                 amounts_by_invoice[invoice.id]['total_currency']) *
                (inv_move_line.amount_currency))
        return new_line_amount_curr

    def _create_vat_on_payment_move(self, cr, uid, bank_line, mv_line_dicts,
                                    context=None):
        move_line_pool = self.pool['account.move.line']
        move_pool = self.pool['account.move']
        voucher_pool = self.pool['account.voucher']
        inv_pool = self.pool['account.invoice']
        vat_config_error = bank_line.company_id.vat_config_error
        if not bank_line.journal_id.vat_on_payment_related_journal_id:
            if vat_config_error == 'raise_error':
                raise orm.except_orm(
                    _('Error'),
                    _("We are on a VAT on payment treatment "
                      "but journal %s does not have a related shadow "
                      "journal")
                    % bank_line.journal_id.name)
            else:
                real_journal = bank_line.journal_id.id
        else:
            real_journal = (
                bank_line.journal_id.vat_on_payment_related_journal_id.id)

        amounts_by_invoice = self.allocated_amounts_grouped_by_invoice(
            cr, uid, bank_line, mv_line_dicts, context)

        lines_to_create = []
        for inv_id in amounts_by_invoice:
            invoice = inv_pool.browse(cr, uid, inv_id, context)
            for inv_move_line in invoice.move_id.line_id:
                if (
                    inv_move_line.account_id.type != 'receivable' and
                    inv_move_line.account_id.type != 'payable'
                ):
                    new_line_amount = self._compute_new_line_amount(
                        cr, uid, bank_line, inv_move_line,
                        amounts_by_invoice, invoice, context=context)
                    new_line_amount_curr = (
                        self._compute_new_line_currency_amount(
                            cr, uid, inv_move_line, amounts_by_invoice,
                            invoice, context=context)
                    )
                    foreign_currency_id = amounts_by_invoice[
                        invoice.id]['foreign_currency_id']
                    real_vals = voucher_pool._prepare_real_move_line(
                        cr, uid, inv_move_line, new_line_amount,
                        new_line_amount_curr, foreign_currency_id,
                        context=context)
                    lines_to_create.append(real_vals)

                    shadow_vals = voucher_pool._prepare_shadow_move_line(
                        cr, uid, inv_move_line, new_line_amount,
                        context=context)
                    lines_to_create.append(shadow_vals)

        ctx = dict(context) or {}
        ctx['journal_id'] = real_journal
        ctx['period_id'] = bank_line.statement_id.period_id.id
        ctx['date'] = bank_line.statement_id.date
        shadow_move_id = move_pool.create(
            cr, uid, voucher_pool._prepare_shadow_move(
                cr, uid, bank_line, move_id_field='journal_entry_id',
                context=ctx), ctx)

        if bank_line.company_id.vat_payment_lines == 'shadow_move':
            self._move_payment_lines_to_shadow_entry(
                cr, uid, bank_line, shadow_move_id, context=ctx)

        for line_to_create in lines_to_create:
            line_to_create['move_id'] = shadow_move_id
            if (
                line_to_create['type'] == 'real' and
                bank_line.company_id.vat_payment_lines == 'shadow_move'
            ):
                line_to_create['move_id'] = bank_line.journal_entry_id.id
            del line_to_create['type']

            move_line_pool.create(cr, uid, line_to_create, ctx)

        bank_line.write({'shadow_move_id': shadow_move_id})

        voucher_pool.balance_move(
            cr, uid, shadow_move_id, ctx)
        voucher_pool.balance_move(
            cr, uid, bank_line.journal_entry_id.id, ctx)

        return True

    def _move_payment_lines_to_shadow_entry(
        self, cr, uid, bank_line, shadow_move_id, context=None
    ):
        for line in bank_line.journal_entry_id.line_id:
            if line.account_id.type != 'liquidity':
                # difference with voucher: here we don't have
                # 'exclude_write_off', so it can't be set to true and
                # write off line must always be moved to shadow move
                line.write({
                    'move_id': shadow_move_id,
                }, update_check=False)
                # this will allow user to see the real entry from
                # invoice payment tab
                if (line.account_id.type == 'receivable' or
                        line.account_id.type == 'payable'):
                    line.write({
                        'real_payment_move_id': bank_line.journal_entry_id.id,
                    })
        return True

    def process_reconciliation(self, cr, uid, id, mv_line_dicts,
                               context=None):
        if context is None:
            context = {}
        journal_pool = self.pool.get('account.journal')
        st_line = self.browse(cr, uid, id, context=context)
        entry_posted = st_line.journal_id.entry_posted
        # see action_move_line_create of voucher
        if entry_posted:
            journal_pool.write(
                cr, uid, st_line.journal_id.id, {'entry_posted': False})
        # because process_reconciliation changes mv_line_dicts
        original_mv_line_dicts = copy.deepcopy(mv_line_dicts)
        res = super(AccountBankStatementLine, self).process_reconciliation(
            cr, uid, id, mv_line_dicts, context=context)
        st_line.refresh()
        is_vat_on_payment = self.is_vat_on_payment(
            cr, uid, original_mv_line_dicts)
        if is_vat_on_payment:
            self._create_vat_on_payment_move(
                cr, uid, st_line, original_mv_line_dicts, context=context)
        if entry_posted:
            journal_pool.write(
                cr, uid, st_line.journal_id.id, {'entry_posted': True})
            st_line.journal_entry_id.post()
            if is_vat_on_payment:
                st_line.shadow_move_id.post()
        return res

    def cancel(self, cr, uid, ids, context=None):
        res = super(AccountBankStatementLine, self).cancel(
            cr, uid, ids, context)
        self.pool['account.voucher'].unreconcile_documents(
            cr, uid, ids, model='account.bank.statement.line', context=context)
        return res

    def get_write_off_vals(self, cr, uid, mv_line_dicts, context=None):
        """
        Assuming we will have only one item of mv_line_dicts without
        counterpart_move_line_id
        """
        write_off_list = []
        for mv_line_dict in mv_line_dicts:
            if not mv_line_dict.get('counterpart_move_line_id'):
                if mv_line_dict not in write_off_list:
                    write_off_list.append(mv_line_dict)
        if len(write_off_list) > 1:
            raise orm.except_orm(
                _("Error"),
                _("Can't handle write-off with more than 1 move line without"
                  " counterpart_move_line_id"))
        if write_off_list:
            return write_off_list[0]
        else:
            return {}

    def allocated_amounts_grouped_by_invoice(
        self, cr, uid, bank_line, mv_line_dicts, context=None
    ):
        '''
        See allocated_amounts_grouped_by_invoice method of accout.voucher
        '''

        res = {}
        if context is None:
            context = {}
        ctx = context.copy()
        ctx['date'] = bank_line.date
        company_currency = bank_line.journal_id.company_id.currency_id
        statement_currency = bank_line.journal_id.currency or company_currency
        current_currency = bank_line.currency_id or statement_currency
        move_line_model = self.pool['account.move.line']
        voucher_model = self.pool['account.voucher']
        currency_obj = self.pool.get('res.currency')
        write_off_vals = self.get_write_off_vals(
            cr, uid, mv_line_dicts, context=context)

        for mv_line_dict in mv_line_dicts:
            if (
                mv_line_dict.get('is_tax_line') or not
                mv_line_dict.get('counterpart_move_line_id')
            ):
                continue
            counterpart_move_line = move_line_model.browse(
                cr, uid, mv_line_dict['counterpart_move_line_id'],
                context=context)
            if counterpart_move_line.invoice:
                if counterpart_move_line.invoice.id not in res:
                    res[counterpart_move_line.invoice.id] = {
                        'allocated': 0.0,
                        'total': 0.0,
                        'total_currency': 0.0,
                        'write-off': 0.0,
                        'allocated_currency': 0.0,
                        'foreign_currency_id': False,
                        'currency-write-off': 0.0,
                    }
                # mv_line_dict contains the amount in statement currency
                amount_currency = (
                    mv_line_dict.get('debit') or mv_line_dict.get('credit'))
                current_amount = amount_currency
                res[counterpart_move_line.invoice.id][
                    'total'
                ] = voucher_model.get_invoice_total(
                    counterpart_move_line.invoice)
                if company_currency.id != current_currency.id:
                    current_amount = currency_obj.compute(
                        cr, uid, current_currency.id, company_currency.id,
                        amount_currency, context=ctx)
                    res[counterpart_move_line.invoice.id][
                        'allocated_currency'
                    ] += amount_currency
                    res[counterpart_move_line.invoice.id][
                        'foreign_currency_id'
                    ] = current_currency.id
                    res[counterpart_move_line.invoice.id][
                        'total_currency'
                    ] = voucher_model.get_invoice_total_currency(
                        counterpart_move_line.invoice)
                # allocated amount includes write-off
                res[counterpart_move_line.invoice.id][
                    'allocated'
                ] += current_amount

        if res:
            # mv_line_dicts contains currency values
            currency_write_off_amount = (
                write_off_vals.get('credit', 0) -
                write_off_vals.get('debit', 0)
                )
            currency_write_off_per_invoice = (
                currency_write_off_amount / len(res))
            if not bank_line.company_id.allow_distributing_write_off and len(
                res
            ) > 1 and currency_write_off_per_invoice:
                raise orm.except_orm(_('Error'), _(
                    'You are trying to pay with write-off more than one '
                    'invoice and distributing write-off is not allowed. '
                    'See company settings.'))
            if bank_line.amount < 0:
                currency_write_off_per_invoice = (
                    - currency_write_off_per_invoice)
            for inv_id in res:
                res[inv_id][
                    'currency-write-off'
                ] = currency_write_off_per_invoice
                if company_currency.id != current_currency.id:
                    res[inv_id]['write-off'] = currency_obj.compute(
                        cr, uid, current_currency.id, company_currency.id,
                        currency_write_off_per_invoice, context=ctx)
                else:
                    res[inv_id]['write-off'] = currency_write_off_per_invoice

        return res
