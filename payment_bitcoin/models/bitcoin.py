# -*- coding: utf-8 -*-
# © initOS GmbH 2016
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, _
from openerp.exceptions import except_orm
from hashlib import sha256
import requests

from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging
_logger = logging.getLogger('payment_bitcoin')

digits58 = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'


def decode_base58(bc, length):
    n = 0
    for char in bc:
        n = n * 58 + digits58.index(char)
    return ('%%0%dx' % (length << 1) % n).decode('hex')[-length:]


def validate_bitcoin_address(address):
    bcbytes = decode_base58(address, 25)
    return bcbytes[-4:] == sha256(sha256(bcbytes[:-4]).digest()).digest()[:4]


class bitcoin_address(models.Model):
    # Store Bitcoin addresses,
    # address will be checked for Unique and Valid Bitcoin address
    # once used, it'll have order_id assigned, so it won't use again.
    _name = 'bitcoin.address'

    name = fields.Char('Address', required=True)
    create_date = fields.Datetime('Created')
    create_uid = fields.Many2one('res.users', 'Created by')

    order_id = fields.Many2one(
        'sale.order',
        'Order Assigned',
        ondelete='set null')

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Bitcoin Address must be Unique'),
    ]

    @api.multi
    def _check_bitcoin_address(self):
        for obj in self:
            if not validate_bitcoin_address(obj.name):
                raise except_orm(
                    _('Invalid Bitcoin Address'),
                    _("Bitcoin Address '%s' doesn't seem to valid Bitcoin Address")
                    % obj.name)
                return False
        return True

    _constraints = [
        (_check_bitcoin_address, 'Check Bitcoin Address', ['name']),
    ]


class bitcoin_rate(models.Model):
    # This stores URL for rate lookup and other related key configuration.
    _name = 'bitcoin.rate'

    url = fields.Char(
        'Bitcoin Rate URL',
        default=
        'https://blockchain.info/tobtc?currency={CURRENCY}&value={AMOUNT}'
    )
    rate_lines = fields.One2many('bitcoin.rate.line', 'rate_id', 'Rates')

    markup = fields.Float('Markup (%)')
    unit = fields.Selection([('BTC', 'BTC'), ('mBTC', 'mBTC')],
                            'Display Unit', default='mBTC')
    valid_minutes = fields.Integer(
        'Rate Valid For (Minutes)',
        default=20,
        help=
        "after this minutes rate will be checked again for same amount")

    @api.model
    def get_rate(self, order_id=False, order_ref=False):
        # function returns bitcoin rate and address
        # for the order currency and total amount
        sobjs = self.search([])
        if len(sobjs) != 1:
            return False
        sobj = sobjs[0]

        if order_id:
            order_obj = self.env['sale.order'].sudo().browse(int(order_id))
        elif order_ref:
            orders = self.env['sale.order'].\
                search([('name', '=', order_ref)])
            if not orders:
                return False
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
                return False

        valid_rate_exists = self.env['bitcoin.rate.line'].\
            sudo().search([('order_id', '=', order_obj.id),
                           ('currency_id', '=', currency.id),
                           ('amount', '=', amount_total),
                           ('create_date', '>=',
                            (datetime.now()-relativedelta(minutes=sobj.valid_minutes)).
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
                return False

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


class bitcoin_rate_line(models.Model):
    # Store Log Rate lookup lines
    _name = 'bitcoin.rate.line'
    _order = 'create_date desc'

    rate_id = fields.Many2one('bitcoin.rate', 'Bitcoin Rate')
    create_date = fields.Datetime('Create Date')
    rate = fields.Float('BTC', digits=(20, 8))

    currency_id = fields.Many2one('res.currency', 'Currency')
    amount = fields.Float('Amount')
    order_id = fields.Integer('Order ID')


class payment_transaction(models.Model):
    _inherit = 'payment.transaction'

    bitcoin_address = fields.Char('Bitcoin Address')
    bitcoin_amount = fields.Float('Bitcoin Amount')
