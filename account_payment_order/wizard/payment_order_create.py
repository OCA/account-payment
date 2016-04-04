# -*- coding: utf-8 -*-
# (c) 2015 brain-tec AG (http://www.braintec-group.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml import etree

from openerp import models, fields, api, _


class PaymentOrderCreate(models.TransientModel):
    """
    Create a payment object with lines corresponding to the account move line
    to pay according to the date and the mode provided by the user.
    Hypothesis:
    - Small number of non-reconciled move line, payment mode and
    bank account type,
    - Big number of partner and bank account.

    If a type is given, unsuitable account Entry lines are ignored.
    """

    _name = 'payment.order.create'
    _description = 'payment.order.create'

    duedate = fields.Date('Due Date', required=True,
                          default=fields.Date.today)

    entries = fields.Many2many('account.move.line')

    populate_results = fields.Boolean(string="Populate results directly",
                                      default=True)

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(PaymentOrderCreate, self).\
            fields_view_get(view_id=view_id, view_type=view_type,
                            toolbar=toolbar, submenu=False)

        context = dict(self._context or {})
        if context and 'line_ids' in context:
            doc = etree.XML(res['arch'])
            nodes = doc.xpath("//field[@name='entries']")
            for node in nodes:
                node.set('domain', '[("id", "in", ' +
                         str(context['line_ids']) + ')]')
            res['arch'] = etree.tostring(doc)
        return res

    @api.multi
    def create_payment(self):
        """This method is a slightly modified version of the existing method on
        this model in account_payment.
        - pass the payment mode to line2bank()
        - allow invoices to create influence on the payment process: not only
          'Free' references are allowed, but others as well
        - check date_to_pay is not in the past.
        """
        if not self.entries:
            return {'type': 'ir.actions.act_window_close'}
        context = self.env.context
        payment_line_obj = self.env['payment.line']
        payment = self.env['payment.order'].browse(context['active_id'])
        # Populate the current payment with new lines:
        for line in self.entries:
            vals = self._prepare_payment_line(payment, line)
            payment_line_obj.create(vals)
        # Force reload of payment order view as a workaround for lp:1155525
        return {'name': _('Payment Orders'),
                'context': context,
                'view_type': 'form',
                'view_mode': 'form,tree',
                'res_model': 'payment.order',
                'res_id': context['active_id'],
                'type': 'ir.actions.act_window'}

    @api.multi
    def search_entries(self):
        """This method taken from account_payment module.
        We adapt the domain based on the payment_order_type
        """
        line_obj = self.env['account.move.line']
        model_data_obj = self.env['ir.model.data']
        # -- start account_banking_payment --
        payment = self.env['payment.order'].browse(
            self.env.context['active_id'])
        # Search for move line to pay:
        domain = [('move_id.state', '=', 'posted'),
                  ('reconciled', '=', False),
                  ('company_id', '=', payment.mode.company_id.id),
                  '|',
                  ('date_maturity', '<=', self.duedate),
                  ('date_maturity', '=', False)]
        self.extend_payment_order_domain(payment, domain)
        # -- end account_direct_debit --
        lines = line_obj.search(domain)
        context = self.env.context.copy()
        context['line_ids'] = self.filter_lines(lines)
        context['populate_results'] = self.populate_results
        if payment.payment_order_type == 'payment':
            context['display_credit'] = True
            context['display_debit'] = False
        else:
            context['display_credit'] = False
            context['display_debit'] = True
        model_datas = model_data_obj.search(
            [('model', '=', 'ir.ui.view'),
             ('name', '=', 'view_payment_order_create_lines')])
        return {'name': _('Entry Lines'),
                'context': context,
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'payment.order.create',
                'views': [(model_datas[0].res_id, 'form')],
                'type': 'ir.actions.act_window',
                'target': 'new',
                }

    @api.model
    def default_get(self, field_list):
        res = super(PaymentOrderCreate, self).default_get(field_list)
        context = self.env.context
        if ('entries' in field_list and context.get('line_ids') and
                context.get('populate_results')):
            res.update({'entries': context['line_ids']})
        return res

    @api.multi
    def extend_payment_order_domain(self, payment_order, domain):
        self.ensure_one()
        if payment_order.payment_order_type == 'payment':
            # For payables, propose all unreconciled credit lines,
            # including partially reconciled ones.
            # If they are partially reconciled with a supplier refund,
            # the residual will be added to the payment order.
            #
            # For receivables, propose all unreconciled credit lines.
            # (ie customer refunds): they can be refunded with a payment.
            # Do not propose partially reconciled credit lines,
            # as they are deducted from a customer invoice, and
            # will not be refunded with a payment.
            domain += [('credit', '>', 0),
                       '|',
                       ('account_id.user_type_id.type', '=', 'payable'),
                       '&',
                       ('account_id.user_type_id.type', '=', 'receivable'),
                       ('full_reconcile_id.partial_reconcile_ids', '=', False)]

    @api.multi
    def filter_lines(self, lines):
        """ Filter move lines before proposing them for inclusion
            in the payment order.

        This implementation filters out move lines that are already
        included in draft or open payment orders. This prevents the
        user to include the same line in two different open payment
        orders. When the payment order is sent, it is assumed that
        the move will be reconciled soon (or immediately with
        account_banking_payment_transfer), so it will not be
        proposed anymore for payment.

        See also https://github.com/OCA/bank-payment/issues/93.

        :param lines: recordset of move lines
        :returns: list of move line ids
        """
        self.ensure_one()
        payment_lines = self.env['payment.line'].\
            search([('order_id.state', 'in', ('draft', 'open')),
                    ('move_line_id', 'in', lines.ids)])
        to_exclude = set([l.move_line_id.id for l in payment_lines])
        return [l.id for l in lines if l.id not in to_exclude]

    @api.multi
    def _prepare_payment_line(self, payment, line):
        """This function is designed to be inherited
        The resulting dict is passed to the create method of payment.line"""
        self.ensure_one()
        _today = fields.Date.context_today(self)
        date_to_pay = False  # no payment date => immediate payment
        if payment.date_prefered == 'due':
            # -- account_banking
            # date_to_pay = line.date_maturity
            date_to_pay = (
                line.date_maturity
                if line.date_maturity and line.date_maturity > _today
                else False)
            # -- end account banking
        elif payment.date_prefered == 'fixed':
            # -- account_banking
            # date_to_pay = payment.date_scheduled
            date_to_pay = (
                payment.date_scheduled
                if payment.date_scheduled and payment.date_scheduled > _today
                else False)
            # -- end account banking
        # -- account_banking
        state = 'normal'
        communication = line.ref or '-'
        if line.invoice_id:
            if line.invoice_id.type in ('in_invoice', 'in_refund'):
                if line.invoice_id.reference_type == 'structured':
                    state = 'structured'
                    communication = line.invoice_id.reference
                else:
                    if line.invoice_id.reference:
                        communication = line.invoice_id.reference
            else:
                # Make sure that the communication includes the
                # customer invoice number (in the case of debit order)
                communication = line.invoice_id.number.replace('/', '')
                state = 'structured'
        amount_currency = line.amount_residual_currency if line.currency_id else line.amount_residual
        line2bank = line.line2bank()
        # -- end account banking
        res = {'move_line_id': line.id,
               'amount_currency': abs(amount_currency),
               'bank_id': line2bank.get(line.id),
               'order_id': payment.id,
               'partner_id': line.partner_id and line.partner_id.id or False,
               # account banking
               'communication': communication,
               'state': state,
               # end account banking
               'date': date_to_pay,
               'currency_id': (line.invoice_id and line.invoice_id.currency_id.id or
                            line.journal_id.currency.id or
                            line.journal_id.company_id.currency_id.id)}
        return res
