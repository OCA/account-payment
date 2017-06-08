# -*- coding: utf-8 -*-
# (c) 2015 brain-tec AG (http://www.braintec-group.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import time
from openerp import models, fields, api


class PaymentLine(models.Model):
    _name = 'payment.line'
    _description = 'Payment Line'

    def translate(self, orig):
        return {"due_date": "date_maturity",
                "reference": "ref"}.get(orig, orig)

    def _info_owner(self, name=None):
        result = {}
        for line in self:
            owner = line.order_id.mode.bank_id.partner_id
            result[line.id] = self._get_info_partner(owner)
        return result

    def _get_info_partner(self, partner_record):
        if not partner_record:
            return False
        st = partner_record.street or ''
        st1 = partner_record.street2 or ''
        zip1 = partner_record.zip or ''
        city = partner_record.city or ''
        zip_city = zip1 + ' ' + city
        cntry = (partner_record.country_id and
                 partner_record.country_id.name or '')
        return (partner_record.name + "\n" + st + " " + st1 + "\n" +
                zip_city + "\n" + cntry)

    def _info_partner(self, name=None):
        result = {}
        for line in self:
            result[line.id] = False
            if not line.partner_id:
                break
            result[line.id] = self._get_info_partner(line.partner_id)
        return result

    @api.multi
    def _compute_amount(self):
        for pl in self:
            pl.amount = pl.amount_currency
            if pl.company_currency and pl.currency_id:
                ctx = {
                    'date': pl.order_id.date_done or time.strftime('%Y-%m-%d')
                }
                pl.amount = pl.with_context(ctx).currency_id.\
                    compute(pl.amount_currency, pl.company_currency)

    name = fields.Char('Your Reference', required=True, default=lambda self:
                       self.env['ir.sequence'].next_by_code('payment.line'),
                       copy=False
                       )

    communication = fields.Char('Communication', required=True,
                                help="Used as the message between ordering "
                                "customer and current company. Depicts "
                                "'What do you want to say to the recipient "
                                "about this order ?'"
                                )

    communication2 = fields.Char('Communication 2',
                                 help='The successor message of Communication'
                                 )

    move_line_id = fields.\
        Many2one('account.move.line', 'Entry line',
                 domain=[('reconciled', '=', False),
                         ('account_id.internal_type', '=', 'payable')],
                 help='This Entry Line will be referred for the information of'
                      ' the ordering customer.')

    amount_currency = fields.Float('Amount in Partner Currency',
                                   digits=(16, 2), required=True,
                                   help='Payment amount in the partner '
                                   'currency')

    currency_id = fields.Many2one('res.currency', 'Partner Currency',
                                  required=True, oldname='currency')

    company_currency = fields.Many2one('res.currency', 'Company Currency',
                                       readonly=True,
                                       default=lambda self: self.env.user.
                                       company_id.currency_id.id)

    bank_id = fields.Many2one('res.partner.bank', 'Destination Bank Account')

    order_id = fields.Many2one('payment.order', 'Order', required=True,
                               ondelete='cascade', index=True)

    partner_id = fields.Many2one('res.partner', string="Partner",
                                 required=True,
                                 help='The Ordering Customer')

    amount = fields.Float(compute="_compute_amount",
                          string='Amount in Company Currency',
                          help='Payment amount in the company currency')

    ml_date_created = fields.Datetime(related="move_line_id.create_date",
                                      string="Effective Date",
                                      help="Invoice Effective Date")

    ml_maturity_date = fields.Date(related="move_line_id.date_maturity",
                                   string='Due Date')

    ml_inv_ref = fields.Many2one('account.invoice',
                                 related="move_line_id.invoice_id",
                                 string='Invoice Ref.')

    info_owner = fields.Text(compute="_info_owner", string="Owner Account",
                             help='Address of the Main Partner')

    info_partner = fields.Text(compute="_info_partner",
                               string="Destination Account",
                               help='Address of the Ordering Customer.')

    date = fields.Date('Payment Date',
                       help="If no payment date is specified, the bank will "
                       "treat this payment line directly",
                       default=lambda self: fields.Date.today)

    state = fields.Selection([('normal', 'Free'),
                              ('structured', 'Structured')],
                             'Communication Type', required=True,
                             default='normal')

    bank_statement_line_id = fields.Many2one('account.bank.statement.line',
                                             'Bank statement line')

    company_id = fields.Many2one('res.company', related='order_id.company_id',
                                 string='Company', store=True, readonly=True)

    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name)', 'The payment line name must be unique!'),
    ]
