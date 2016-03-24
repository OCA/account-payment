# -*- coding: utf-8 -*-
# (c) 2015 brain-tec AG (http://www.braintec-group.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import time
from openerp import models, fields, api


class PaymentOrder(models.Model):
    _name = 'payment.order'
    _description = 'Payment Order'
    _rec_name = 'reference'
    _order = 'id desc'

    @api.multi
    @api.depends('line_ids')
    def _compute_total(self):
        for payment_order in self:
            payment_order.total = sum(payment_order.mapped('line_ids.amount'))

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
