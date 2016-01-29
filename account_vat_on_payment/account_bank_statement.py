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

    def _move_payment_lines_to_shadow_entry(
        self, cr, uid, bank_line, shadow_move_id, context=None
    ):
        for line in bank_line.journal_entry_id.line_id:
            if line.account_id.type != 'liquidity':
                # If the line is related to write-off and user doesn't
                # want to compute the tax including write-off,
                # write-off move line must stay on the real move
                line.write({'move_id': shadow_move_id}, update_check=False)
                # this will allow user to see the real entry from
                # invoice payment tab
                if (line.account_id.type == 'receivable' or
                        line.account_id.type == 'payable'):
                    line.write({
                        'real_payment_move_id': bank_line.journal_entry_id.id,
                    })
        return True

    def _create_vat_on_payment_move(self, cr, uid, bank_line, mv_line_dicts,
                                    context=None):
        move_line_pool = self.pool.get('account.move.line')
        move_pool = self.pool.get('account.move')
        currency_pool = self.pool.get('res.currency')
        voucher_pool = self.pool['account.voucher']
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
        company_currency = bank_line.journal_id.company_id.currency_id
        statement_currency = bank_line.journal_id.currency or company_currency
        st_line_currency = bank_line.currency_id or statement_currency
        lines_to_create = []
        for mv_line_dict in mv_line_dicts:
            if (
                mv_line_dict.get('is_tax_line') or not
                mv_line_dict.get('counterpart_move_line_id')
            ):
                continue
            mv_line = move_line_pool.browse(
                cr, uid,
                mv_line_dict['counterpart_move_line_id'],
                context=context)
            invoice = mv_line.invoice

            # mv_line_dict contains the amount in statement currency
            amount_currency = mv_line_dict['debit'] - mv_line_dict['credit']
            currency_id = st_line_currency.id

            # if foreign currency statement, get paid amount at
            # base currency, using statement date
            ctx = context.copy()
            ctx['date'] = bank_line.statement_id.date
            if currency_id != company_currency.id:
                paid_amount = currency_pool.compute(
                    cr, uid, currency_id, company_currency.id,
                    amount_currency,
                    context=ctx)
            else:
                paid_amount = amount_currency

            for inv_move_line in invoice.move_id.line_id:
                if inv_move_line.real_tax_code_id:
                    new_line_amount = currency_pool.round(
                        cr, uid,
                        company_currency,
                        (paid_amount / (mv_line.debit - mv_line.credit)) *
                        (inv_move_line.debit - inv_move_line.credit))
                    if (
                        currency_id != company_currency.id and
                        invoice.currency_id.id != company_currency.id
                    ):
                        new_line_amount_curr = ((
                            amount_currency / mv_line.amount_currency) *
                            inv_move_line.amount_currency)
                        new_currency_id = currency_id
                    else:
                        new_line_amount_curr = 0.00
                        new_currency_id = False
                    real_vals = voucher_pool._prepare_real_move_line(
                        cr, uid, inv_move_line, new_line_amount,
                        new_line_amount_curr, new_currency_id,
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

        return True

    def _move_payment_lines_to_shadow_entry(
        self, cr, uid, bank_line, shadow_move_id, context=None
    ):
        for line in bank_line.journal_entry_id.line_id:
            if line.account_id.type != 'liquidity':
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
