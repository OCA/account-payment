# -*- coding: utf-8 -*-
# © 2011-2012 Domsense s.r.l. (<http://www.domsense.com>).
# © 2014 Agile Business Group sagl (<http://www.agilebg.com>)
# © 2015 Forest and Biomass Services Romania (<https://www.forbiom.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.osv import orm, fields
from openerp.tools.translate import _
from openerp.tools import float_is_zero


class AccountBankStatementLine(orm.Model):
    _inherit = "account.bank.statement.line"

    _columns = {
        'shadow_move_id': fields.many2one(
            'account.move', 'Shadow Entry', readonly=True),
    }

    def is_vat_on_payment(self, mv_line_dicts):
        move_line_pool = self.pool.get('account.move.line')
        vat_on_p = 0
        valid_lines = 0
        for mv_line_dict in mv_line_dicts:
            valid_lines += 1
            if mv_line_dict.get('is_tax_line'):
                continue
            mv_line = move_line_pool.browse(
                self.cr, self.uid,
                mv_line_dict['counterpart_move_line_id'])
            invoice = mv_line.invoice
            if invoice.vat_on_payment:
                vat_on_p += 1
        if vat_on_p and vat_on_p != valid_lines:
            raise orm.except_orm(
                _('Error'),
                _("Can't handle VAT on payment if not every invoice "
                  "is on a VAT on payment treatment"))
        return vat_on_p

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
            'partner_id': (inv_move_line.partner_id and
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
        self, cr, uid, inv_move_line, new_line_amount, context=None
    ):
        if inv_move_line.account_id.id == inv_move_line.real_account_id.id:
            line_amount = 0.00
        else:
            line_amount = new_line_amount
        vals = {
            'name': inv_move_line.name,
            'account_id': inv_move_line.account_id.id,
            'credit': (inv_move_line.debit and line_amount or 0.0),
            'debit': (inv_move_line.credit and line_amount or 0.0),
            'type': 'shadow',
            'partner_id': (inv_move_line.partner_id and
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

    def _prepare_shadow_move(self, cr, uid, bank_line, context=None):
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
        return {
            'journal_id': real_journal,
            'period_id': bank_line.statement_id.period_id.id,
            'date': bank_line.statement_id.date,
        }

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
            if mv_line_dict.get('is_tax_line'):
                continue
            mv_line = move_line_pool.browse(
                cr, uid,
                mv_line_dict['counterpart_move_line_id'],
                context=context)
            invoice = mv_line.invoice
            ctx = context.copy()
            ctx['date'] = mv_line.date
            amount_currency = mv_line_dict['debit'] - mv_line_dict['credit']
            currency_id = st_line_currency.id
            if mv_line.currency_id.id == currency_id \
                and float_is_zero(
                    abs(mv_line.amount_currency) - abs(amount_currency),
                    precision_rounding=mv_line.currency_id.rounding):
                debit_at_old_rate = mv_line.credit
                credit_at_old_rate = mv_line.debit
            else:
                debit_at_old_rate = currency_pool.compute(
                    cr, uid, st_line_currency.id, company_currency.id,
                    mv_line_dict['debit'], context=ctx)
                credit_at_old_rate = currency_pool.compute(
                    cr, uid, st_line_currency.id, company_currency.id,
                    mv_line_dict['credit'], context=ctx)

            pay_amount = credit_at_old_rate or debit_at_old_rate

            for inv_move_line in invoice.move_id.line_id:
                if inv_move_line.real_tax_code_id:
                    new_line_amount = currency_pool.round(
                        cr, uid,
                        company_currency,
                        (pay_amount / invoice.amount_total) *
                        inv_move_line.tax_amount)
                    if (currency_id != company_currency.id):
                        new_line_amount_curr = -1 * ((
                            pay_amount / invoice.amount_total) *
                            inv_move_line.tax_amount)
                        new_currency_id = currency_id
                    else:
                        new_line_amount_curr = 0.00
                        new_currency_id = False
                    real_vals = self._prepare_real_move_line(
                        cr, uid, inv_move_line, new_line_amount,
                        new_line_amount_curr, new_currency_id,
                        context=context)
                    lines_to_create.append(real_vals)

                    shadow_vals = self._prepare_shadow_move_line(
                        cr, uid, inv_move_line, new_line_amount,
                        context=context)
                    lines_to_create.append(shadow_vals)
        ctx = dict(context) or {}
        ctx['journal_id'] = real_journal
        ctx['period_id'] = bank_line.statement_id.period_id.id
        ctx['date'] = bank_line.statement_id.date
        shadow_move_id = move_pool.create(
            cr, uid, self._prepare_shadow_move(
                cr, uid, bank_line, context=ctx), ctx)

        for line_to_create in lines_to_create:
            if line_to_create['type'] == 'real':
                if bank_line.company_id.vat_payment_lines == 'shadow_move':
                    line_to_create['move_id'] = shadow_move_id
                else:
                    line_to_create['move_id'] = shadow_move_id
            elif line_to_create['type'] == 'shadow':
                line_to_create['move_id'] = shadow_move_id
            del line_to_create['type']

            move_line_pool.create(cr, uid, line_to_create, ctx)

        bank_line.write({'shadow_move_id': shadow_move_id})
        return True

    def process_reconciliation(self, cr, uid, id, mv_line_dicts,
                               context=None):
        if context is None:
            context = {}
        st_line = self.browse(cr, uid, id, context=context)
        self._create_vat_on_payment_move(cr, uid, st_line, mv_line_dicts,
                                         context=context)
        res = super(AccountBankStatementLine, self).process_reconciliation(
            cr, uid, id, mv_line_dicts, context=context)
        if st_line.shadow_move_id:
            st_line.shadow_move_id.post()
        return res

    def cancel(self, cr, uid, ids, context=None):
        res = super(AccountBankStatementLine, self).cancel(
            cr, uid, ids, context)
        reconcile_pool = self.pool.get('account.move.reconcile')
        move_pool = self.pool.get('account.move')
        for st_line in self.browse(cr, uid, ids, context=context):
            recs = []
            if st_line.shadow_move_id:
                for line in st_line.shadow_move_id.line_id:
                    if line.reconcile_id:
                        recs += [line.reconcile_id.id]
                    if line.reconcile_partial_id:
                        recs += [line.reconcile_partial_id.id]

                reconcile_pool.unlink(cr, uid, recs)

                if st_line.shadow_move_id:
                    move_pool.button_cancel(
                        cr, uid, [st_line.shadow_move_id.id])
                    move_pool.unlink(cr, uid, [st_line.shadow_move_id.id])
        return res
