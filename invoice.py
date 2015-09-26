# coding: utf-8
from openerp.osv import osv, fields
from datetime import datetime
import logging
import psycopg2

logger = logging.getLogger(__name__)


class Invoice(osv.Model):

    _inherit = 'account.invoice'

    # Just add these two fields to display them on portal invoice
    _columns = {'paid_date': fields.date("Payment date"),
                'paid_amount': fields.float("Amount paid")}

    def get_invoice_id(self, cr, uid, ref, montant, context=None):
        """ search and return invoice id for the given reference """
        invoice_ids = self.search(cr, uid, [('number', '=', ref)])
        if not invoice_ids:
            warning_id = self.pool.get('paybox.warning').create(
                cr, uid, {'ref': ref, 'amount': montant})
            self.pool.get('paybox.warning').send_warning_mail(cr, uid, warning_id, 'invoice')
            return False
        return invoice_ids[0]

    def _portal_payment_block(self, cr, uid, ids, fieldname, arg, context=None):
        """ invoice residual amount is used instead of total amount """
        result = dict.fromkeys(ids, False)
        payment_acquirer = self.pool.get('payment.acquirer')
        for this in self.browse(cr, uid, ids, context=context):
            if(this.type == 'out_invoice' and this.state not in ('draft', 'done')
               and not this.reconciled):
                result[this.id] = payment_acquirer.render_payment_block(
                    cr, uid, this, this.number, this.currency_id, this.residual, context=context)
        return result

    def create_move(self, cr, uid, invoice):
        """ create move with the right values """
        journal = self.pool.get('account.journal')
        period = self.pool.get('account.period')
        move = self.pool.get('account.move')
        today = datetime.today()
        bank_journal_id = journal.search(cr, uid, [('code', '=', 'BNK2')])
        period_id = invoice.period_id.id if invoice else period.find(cr, uid, today)[0]
        values = {'journal_id': bank_journal_id[0], 'period_id': period_id,
                  'date': today, 'name': '/'}
        move_id = move.create(cr, uid, values)
        return move_id

    def create_move_lines(self, cr, uid, invoice, move_id, montant):
        """ create move lines for the given amount and linked to given move_id """
        move_lines = []
        journal = self.pool.get('account.journal')
        period = self.pool.get('account.period')
        account = self.pool.get('account.account')
        move_line = self.pool.get('account.move.line')
        today = datetime.today()
        bank_journal_id = journal.search(cr, uid, [('code', '=', 'BNK2')])
        bank_account_id = account.search(cr, uid, [('code', '=', '512102')])
        customer_account_id = account.search(cr, uid, [('code', '=', '411100')])
        period_id = invoice.period_id.id if invoice else period.find(cr, uid, today)[0]
        partner_id = invoice.partner_id.id if invoice else False
        values = {'journal_id': bank_journal_id[0], 'period_id': period_id,
                  'move_id': move_id, 'date': today, 'credit': montant, 'debit': 0.00,
                  'account_id': customer_account_id[0], 'name': '/',
                  'partner_id': partner_id}
        credit_line_id = move_line.create(cr, uid, values)
        move_lines.append(credit_line_id)
        values = {'journal_id': bank_journal_id[0], 'period_id': period_id,
                  'move_id': move_id, 'date': today, 'debit': montant, 'credit': 0.00,
                  'account_id': bank_account_id[0], 'name': '/',
                  'partner_id': partner_id}
        move_line.create(cr, uid, values)
        return move_lines

    def reconcile(self, cr, uid, invoice, line_id, montant):
        """ try to find the invoice move_line that will be reconciled with the payment line """
        reconcile = self.pool.get('account.move.line.reconcile')
        move_line = self.pool.get('account.move.line')
        move_id = invoice.move_id.id
        move_line_id = move_line.search(
            cr, uid, ['&', ('move_id', '=', move_id), ('debit', '=', montant)])
        if not move_line_id:
            logger.info(
                u"""[Paybox] - Le paiement n'a pas été lettré,
vérifiez les montants et effectuer le lettrage manuellement""")
            warning_id = self.pool.get('paybox.warning').create(
                cr, uid, {'ref': invoice.number, 'amount': montant})
            self.pool.get('paybox.warning').send_warning_mail(cr, uid, warning_id, 'reconcile')
            return False
        line_id.append(move_line_id[0])
        context = {'active_ids': line_id}
        reconcile.trans_rec_reconcile_full(cr, uid, {}, context)
        return True

    def validate_invoice_paybox(self, cr, uid, ref, montant, attempt=0, nocommit=False):
        """ Store payment for the referenced invoice with a specific amount.
            First, we create move and move line then, if the invoice still exists
            and a line is found, the two lines are reconciled """
        # The amount is formatted in cent we need the convert the value
        montant = float(montant)/100
        invoice_id = self.get_invoice_id(cr, uid, ref, montant)
        invoice = self.browse(cr, uid, invoice_id) if invoice_id else False
        if not invoice or invoice.state == 'open':
            move_id = self.create_move(cr, uid, invoice)
            move_line_id = self.create_move_lines(cr, uid, invoice, move_id, montant)
        # nocommit can be used for unit tests
        if not nocommit:
            try:
                if invoice and invoice.state == 'open':
                    self.write(
                        cr, uid, [invoice_id],
                        {'paid_date': datetime.today(), 'paid_amount': montant},
                        {'paybox': True})
                    self.reconcile(cr, uid, invoice, move_line_id, montant)
                cr.commit()
            except psycopg2.extensions.TransactionRollbackError:
                logger.warning(u"Unable to validate invoice", u"TransactionRollbackError catched")
                # just rollback and retry validate the invoice
                if attempt < 10:
                    cr.rollback()
                    return self.validate_invoice_paybox(cr, uid, ref, montant, attempt=attempt+1)
                else:
                    raise psycopg2.TransactionRollbackError
        return invoice_id
