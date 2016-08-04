# -*- coding: utf-8 -*-
# © initOS GmbH 2016
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, _
from openerp.exceptions import except_orm
from hashlib import sha256

digits58 = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'


def decode_base58(bc, length):
    n = 0
    for char in bc:
        n = n * 58 + digits58.index(char)
    return ('%%0%dx' % (length << 1) % n).decode('hex')[-length:]


def validate_bitcoin_address(address):
    bcbytes = decode_base58(address, 25)
    return bcbytes[-4:] == sha256(sha256(bcbytes[:-4]).digest()).digest()[:4]


class BitcoinAddress(models.Model):
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
                    _("Bitcoin Address '%s' doesn't seem \
                     to valid Bitcoin Address") % obj.name)
                return False
        return True

    _constraints = [
        (_check_bitcoin_address, 'Check Bitcoin Address', ['name']),
    ]
