# -*- coding: utf-8 -*-
# (c) 2015 brain-tec AG (http://www.braintec-group.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import time
from openerp import models, fields, api, exceptions, workflow, _

class PaymentOrder(models.Model):
    _name = 'payment.order'
    _description = 'Payment Order'
    _rec_name = 'reference'
    _order = 'id desc'

    @api.depends('line_ids', 'line_ids.amount')
    @api.one
    def _compute_total(self):
        self.total = sum(self.mapped('line_ids.amount') or [0.0])

    date_scheduled = fields.Date('Scheduled Date',
                                 states={'done': [('readonly', True)]},
                                 help='Select a date if you have chosen '
                                 'Preferred Date to be fixed.')

    reference = fields.Char('Reference', required=1,
                            states={'done': [('readonly', True)]},
                            default=lambda self:
                            self.env['ir.sequence'].
                            next_by_code('payment.order'),
                            copy=False)

    mode = fields.Many2one('payment.mode', 'Payment Mode', select=True,
                           required=1, states={'done': [('readonly', True)]},
                           help='Select the Payment Mode to be applied.')

    state = fields.Selection([('draft', 'Draft'),
                              ('cancel', 'Cancelled'),
                              ('open', 'Confirmed'),
                              ('done', 'Done')], 'Status', select=True,
                             copy=False, default='draft',
                             help='When an order is placed the status is '
                             '\'Draft\'.\n Once the bank is confirmed the '
                             'status is set to \'Confirmed\'.\n'
                             'Then the order is paid the status is \'Done\'.')

    line_ids = fields.One2many('payment.line', 'order_id',
                               'Payment lines',
                               states={'done': [('readonly', True)]})

    total = fields.Float(compute='_compute_total', string="Total",store=True)

    user_id = fields.Many2one('res.users', 'Responsible', required=True,
                              states={'done': [('readonly', True)]},
                              default=lambda self: self.env.uid)

    date_prefered = fields.\
        Selection([('now', 'Directly'), ('due', 'Due date'),
                   ('fixed', 'Fixed date')
                   ], "Preferred Date", change_default=True, default='due',
                  required=True, states={'done': [('readonly', True)]},
                  help="Choose an option for the Payment Order:'Fixed'"
                       "stands for a date specified by you.'Directly' stands "
                       "for the direct execution. 'Due date' stands for the "
                       "scheduled date of execution.")

    date_done = fields.Date('Execution Date', readonly=True)

    company_id = fields.Many2one('res.company', related='mode.company_id',
                                 string='Company', store=True, readonly=True)

    entries_test = fields.Many2many('account.move.line', 'test_line_pay_rel',
                                    'pay_id', 'line_id')

    payment_order_type = fields.Selection(
        [('payment', 'Payment'), ('debit', 'Direct debit')],
        'Payment order type', required=True, default='payment',
        readonly=True, states={'draft': [('readonly', False)]})
    
    mode_type = fields.Many2one('payment.mode.type', related='mode.type',
                                string='Payment Type')

    @api.one
    def set_to_draft(self):
        self.write({'state': 'draft'})
#         self.create_workflow()
        return True

    @api.one
    def set_to_confirmed(self):
        self.write({'state': 'open'})
#         self.create_workflow()
        return True

    @api.one
    def set_done(self):
        self.write({'date_done': time.strftime('%Y-%m-%d'), 'state': 'done'})
#         self.signal_workflow('done')
        return True

    @api.one
    def write(self, vals):

        payment_line_obj = self.env['payment.line']
        payment_line_ids = []

        if ((vals.get('date_prefered', False) == 'fixed' and not
             vals.get('date_scheduled', False)) or
                vals.get('date_scheduled', False)):
            for order in self:
                for line in order.line_ids:
                    payment_line_ids.append(line.id)
            payment_line_obj.write(payment_line_ids,
                                   {'date': vals.get('date_scheduled', False)})
        elif vals.get('date_prefered', False) == 'due':
            vals.update({'date_scheduled': False})
            for order in self:
                for line in order.line_ids:
                    payment_line_obj.write([line.id],
                                           {'date': line.ml_maturity_date})
        elif vals.get('date_prefered', False) == 'now':
            vals.update({'date_scheduled': False})
            for order in self:
                for line in order.line_ids:
                    payment_line_ids.append(line.id)
            payment_line_obj.write(payment_line_ids, {'date': False})
        return super(PaymentOrder, self).write(vals)

    @api.multi
    def launch_wizard(self):
        """Search for a wizard to launch according to the type.
        If type is manual. just confirm the order.
        Previously (pre-v6) in account_payment/wizard/wizard_pay.py
        """
        context = self.env.context.copy()
        order = self[0]
        # check if a wizard is defined for the first order
        if order.mode.type and order.mode.type.ir_model_id:
            context['active_ids'] = self.ids
            wizard_model = order.mode.type.ir_model_id.model
            wizard_obj = self.env[wizard_model]
            return {
                'name': wizard_obj._description or _('Payment Order Export'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': wizard_model,
                'domain': [],
                'context': context,
                'type': 'ir.actions.act_window',
                'target': 'new',
                'nodestroy': True,
            }
        else:
            # should all be manual orders without type or wizard model
            for order in self[1:]:
                if order.mode.type and order.mode.type.ir_model_id:
                    raise exceptions.Warning(
                        _('Error'),
                        _('You can only combine payment orders of the same '
                          'type'))
            # process manual payments
            for order_id in self.ids:
                workflow.trg_validate(self.env.uid, 'payment.order',
                                      order_id, 'done', self.env.cr)
            return {}

    @api.multi
    def action_done(self):
        self.write({
            'date_done': fields.Date.context_today(self),
            'state': 'done',
            })
        return True
