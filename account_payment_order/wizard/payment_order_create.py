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
        self.ensure_one()
        order_obj = self.env['payment.order']

        context = dict(self._context or {})
        if not self.entries:
            return {'type': 'ir.actions.act_window_close'}

        order = order_obj.browse(context['active_id'])

        # # Finally populate the current payment with new lines:
        for line in self.entries:
            line2bank = line.line2bank()
            if order.date_prefered == "now":
                # no payment date => immediate payment
                date_to_pay = False
            elif order.date_prefered == 'due':
                date_to_pay = line.date_maturity
            elif order.date_prefered == 'fixed':
                date_to_pay = order.date_scheduled
            self.env['payment.line'].create(
                    {'move_line_id': line.id,
                     'amount_currency': abs(line.amount_residual_currency) or
                                        abs(line.amount_residual),
                     'bank_id': line2bank.get(line.id),
                     'order_id': order.id,
                     'partner_id': line.partner_id.id,
                     'communication': line.ref or '/',
                     'state': ('structured' if line.invoice_id.reference_type
                                               != 'none' else 'normal'),
                     'date': date_to_pay,
                     'currency_id': line.invoice_id.currency_id.id or
                         self.env.user.company_id.currency_id.id,
                    }
            )
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def search_entries(self):
        line_obj = self.env['account.move.line']

        # Search for move line to pay:
        domain = [('reconciled', '=', False),
                  ('account_id.internal_type', '=', 'payable'),
                  ('credit', '>', 0), ('account_id.reconcile', '=', True)]

        domain = domain + ['|', ('date_maturity', '<=', self.duedate),
                           ('date_maturity', '=', False)]

        lines = line_obj.search(domain)

        ctx = self.env.context.copy()
        ctx.update({'line_ids': lines.ids})

        payment_order_view = self.env.ref('account_payment_order.'
                                          'view_payment_order_create_lines')

        return {'name': _('Entry Lines'),
                'context': ctx,
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'payment.order.create',
                # 'view_id': resource_id,
                'views': [(payment_order_view.id, 'form')],
                'type': 'ir.actions.act_window',
                'target': 'new',
                'domain': [('entries', 'in', lines.ids)],
                }
