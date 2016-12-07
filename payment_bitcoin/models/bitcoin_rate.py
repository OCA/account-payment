# -*- coding: utf-8 -*-
# © ZedeS Technologies, initOS GmbH 2016
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api
import requests
from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging
_logger = logging.getLogger('payment_bitcoin')


class BitcoinRate(models.Model):
    # This stores URL for rate lookup and other related key configuration.
    _name = 'bitcoin.rate'

    url = fields.Char(
        'Bitcoin Rate URL',
        default='https://blockchain.info/tobtc?'\
        'currency={CURRENCY}&value={AMOUNT}'
    )
    rate_lines = fields.One2many('bitcoin.rate.line', 'rate_id', 'Rates')

    markup = fields.Float('Markup (%)')
    unit = fields.Selection([('BTC', 'BTC'), ('mBTC', 'mBTC')],
                            'Display Unit', default='mBTC')
    valid_minutes = fields.Integer(
        'Rate Valid For (Minutes)',
        default=20,
        help="after this minutes rate will be checked again for same amount")

    @api.model
    def get_rate(self, order_id=False, order_ref=False):
        # function returns bitcoin rate and address
        # for the order currency and total amount
        sobjs = self.search([])
        if len(sobjs) != 1:
            return (False, 'Multiple configuration not allowed')
        sobj = sobjs[0]

        if order_id:
            order_obj = self.env['sale.order'].sudo().browse(int(order_id))
        elif order_ref:
            orders = self.env['sale.order'].\
                search([('name', '=', order_ref)])
            if not orders:
                return (False, 'Oops, Order not found')
            order_obj = orders[0]

        currency = order_obj.pricelist_id.currency_id
        amount_total = order_obj.amount_total

        addr_ids = self.env['bitcoin.address'].\
            search([('order_id', '=', order_obj.id)], limit=1)
        if not addr_ids:
            addr_ids = self.env['bitcoin.address'].\
                search([('order_id', '=', False)], limit=1)
            if not addr_ids:
                _logger.error('No Bitcoin Address configured')
                return (False, 'We are running out of Bitcoin addresses')

        valid_rate_exists = self.env['bitcoin.rate.line'].\
            sudo().search([('order_id', '=', order_obj.id),
                           ('currency_id', '=', currency.id),
                           ('amount', '=', amount_total),
                           ('create_date', '>=',
                            (datetime.now()-relativedelta(
                                minutes=sobj.valid_minutes)).
                            strftime('%Y-%m-%d %H:%M:00'))])
        if valid_rate_exists:
            # Rate was looked up within valid time limit,
            # so we are using the valid one
            rate = valid_rate_exists[0].rate
        else:
            # Check for New Rate
            url = sobj.url.replace('{CURRENCY}', currency.name).\
                replace('{AMOUNT}', str(amount_total))
            response = requests.get(url)
            if response.status_code != 200:
                _logger.error('can not find Bitcoin exchange rate')
                return (False, 'Unable to find Bitcoin exchange rate')

            rate = float(response.content)
            # rate lookup entry saves in logs
            self.env['bitcoin.rate.line'].sudo().create(
                {'rate_id': sobj.id,
                 'rate': rate,
                 'amount': amount_total,
                 'currency_id': currency.id,
                 'order_id': order_obj.id})
        if addr_ids and rate:
            addr_ids[0].sudo().write(
                {'order_id': order_obj.id})
            b_addr = addr_ids[0].name

            if sobj.markup:
                b_amount = (rate * (sobj.markup/100)) + rate
            else:
                b_amount = rate

            if sobj.unit == 'mBTC':
                b_amount = b_amount * 1000.0

        return (b_addr, round(b_amount, 2))


class BitcoinRateLine(models.Model):
    # Store Log Rate lookup lines
    _name = 'bitcoin.rate.line'
    _order = 'create_date desc'

    rate_id = fields.Many2one('bitcoin.rate', 'Bitcoin Rate')
    create_date = fields.Datetime('Create Date')
    rate = fields.Float('BTC', digits=(20, 8))

    currency_id = fields.Many2one('res.currency', 'Currency')
    amount = fields.Float('Amount')
    order_id = fields.Integer('Order ID')
