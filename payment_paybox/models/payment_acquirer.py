# coding: utf-8
from openerp.osv import osv, fields
import binascii
import hashlib
import logging
from datetime import datetime
from openerp.tools.translate import _
from openerp.tools import float_repr
from urlparse import urljoin

_logger = logging.getLogger(__name__)

URL = [('https://preprod-tpeweb.paybox.com/', 'Test pré-production'),
       ('https://tpeweb.paybox.com/', 'Production'),
       ('https://tpeweb1.paybox.com/', 'Production (secours)')]

class PayboxAcquirer(osv.Model):
    _inherit = 'payment.acquirer'

    HASH = {'SHA512': hashlib.sha512}
    paiement_cgi = 'cgi/MYchoix_pagepaiement.cgi'

    _columns = {'paybox_site': fields.char("Site", size=7),
                'paybox_rank': fields.char("Rank", size=3),
                'paybox_shop_id': fields.char("Shop id", size=9),
                'paybox_key': fields.char("Key", password=True),
                'paybox_hash': fields.selection([('SHA512', 'sha512')], "Hash", select=True),
                'paybox_url': fields.selection(URL, u"URL Paybox", select=True),
                'paybox_return_url': fields.char(u"URL publique du serveur Odoo"),
                'paybox_method': fields.selection([('POST', 'Post'), ('GET', 'Get')], u"Méthode",
                                           select=True),
                'paybox_currency': fields.selection([('978', 'Euro'), ('840', 'US Dollar')], u"Devise",
                                           select=True),
                'paybox_admin_mail': fields.char(u"Email de l'administrateur Paybox"),
            }

    _defaults = {
            'paybox_key': '0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF',
            'paybox_shop_id': '107904482',
            'paybox_rank': '32',
            'paybox_site': '1999888',
            'paybox_hash': 'SHA512',
            'paybox_url': 'https://preprod-tpeweb.paybox.com/',
            'paybox_return_url': 'https://store.company.com',
            'paybox_method': 'POST',
            'paybox_currency': '978',
            'paybox_admin_mail': 'test@company.com',
         }

    def _get_providers(self, cr, uid, context=None):
        providers = super(PayboxAcquirer, self)._get_providers(cr, uid, context=context)
        providers.append(['paybox', 'Paybox'])
        return providers

    def build_paybox_args(self, cr, uid, acquirer, tx_values, context=None):
        reference = tx_values['reference']
        amount = tx_values['amount']
        key = acquirer['paybox_key']
        if not key:
            raise Exception("Paybox payment acquirer has not been configured properly: paybox_key is missing")
        identifiant, devise = acquirer['paybox_shop_id'], acquirer['paybox_currency']
        rang, site = acquirer['paybox_rank'], acquirer['paybox_site']
        _hash = acquirer['paybox_hash']
        porteur = tx_values['partner'].email
        url = acquirer['paybox_url']
        url += self.paiement_cgi
        url_retour = acquirer['paybox_return_url']

        if not url_retour:
            raise Exception("Paybox payment acquirer has not been configured properly: paybox_return_url is missing")

        # the paybox amount need to be formated in cents and zero-padded to be at least 3 characters long
        amount = "%03u" % int(amount*100)
        retour = u"Mt:M;Ref:R;Auto:A;Erreur:E;Signature:K"
        url_effectue = urljoin(url_retour, '/payment/paybox/accept')
        url_annule = urljoin(url_retour, '/payment/paybox/cancel')
        url_refuse = urljoin(url_retour, '/payment/paybox/decline')
        url_ipn = urljoin(url_retour, '/payment/paybox/ipn')
        time = datetime.now().isoformat()
        # we need to concatenate the args to compute the hmac
        args = ('PBX_SITE=' + site + '&PBX_RANG=' + rang +
                '&PBX_HASH=' + _hash + '&PBX_CMD=' + reference +
                '&PBX_IDENTIFIANT=' + identifiant + '&PBX_TOTAL=' + amount +
                '&PBX_DEVISE=' + devise + '&PBX_PORTEUR=' + porteur +
                '&PBX_RETOUR=' + retour + '&PBX_TIME=' + time +
                '&PBX_EFFECTUE=' + url_effectue + '&PBX_REFUSE=' + url_refuse +
                '&PBX_ANNULE=' + url_annule +
                '&PBX_REPONDRE_A=' + url_ipn)
        hmac = self.compute_hmac(key, _hash, args)
        return dict(hmac=hmac, hash=_hash, porteur=porteur, url=url, identifiant=identifiant,
                    rank=rang, site=site, url_ipn=url_ipn, refuse=url_refuse, time=time,
                    devise=devise, retour=retour, annule=url_annule, amount=amount,
                    effectue=url_effectue)

    def compute_hmac(self, key, hash_name, args):
        """ compute hmac with key, hash and args given """
        try:
            binary_key = binascii.unhexlify(key)
        except:
            _logger.exception("Cannot decode key")
            # We may just log this error and not raise exception
            raise osv.except_osv(u"Calcul HMAC impossible", u"Vérifiez la valeur de la clé")

        try:
            import hmac
            hmac_value = hmac.new(binary_key, args, self.HASH[hash_name]).hexdigest().upper()
        except:
            # We may just log this error and not raise exception
            _logger.exception("Calcul HMAC impossible")
            raise osv.except_osv(u"Calcul HMAC impossible", u"Une erreur s'est produite")
        return hmac_value

    def paybox_form_generate_values(self, cr, uid, id, partner_values, tx_values, context=None):
        acquirer = self.browse(cr, uid, id, context=context)
        vals = self.build_paybox_args(
            cr, uid, acquirer, tx_values, context=context)

        tx_values.update(vals)
        return partner_values, tx_values

    def _wrap_payment_block(self, cr, uid, html_block, amount,
                            currency_id, acquirer=None, context=None):
        """ override original method to add the paybox html block """
        if not html_block:
            if acquirer and acquirer == 'Paybox':
                return ''
            else:
                link = '#action=account.action_account_config'
                payment_header = _(""" You can finish the configuration in the
<a href="%s">Bank&Cash settings</a>""") % link
                amount = _('No online payment acquirers configured')
                group_ids = self.pool.get('res.users').browse(
                    cr, uid, uid, context=context).groups_id
                if any(group.is_portal for group in group_ids):
                    return ''
        else:
            payment_header = _('Pay safely online')
            currency_obj = self.pool['res.currency']
            currency = currency_obj.browse(cr, uid, currency_id)
            currency_str = currency.symbol or currency.name
            if acquirer and acquirer == 'Paybox':
                amount_str = float_repr(
                    amount,
                    self.pool.get('decimal.precision').precision_get(cr, uid, 'Account'))
                amount = (u"%s %s" % ((currency_str, amount_str)
                          if currency.position == 'before' else (amount_str, currency_str)))
            else:
                amount_str = float_repr(
                    amount, self.pool.get('decimal.precision').precision_get(cr, uid, 'Account'))
                amount = (u"%s %s" % ((currency_str, amount_str)
                          if currency.position == 'before' else (amount_str, currency_str)))

        result = """<div class="payment_acquirers">
                         <div class="payment_header">
                             <div class="payment_amount">%s</div>
                             %s
                         </div>
                         %%s
                     </div>""" % (amount, payment_header)
        return result % html_block

    def _get_paybox_urls(self, cr, uid, acquirer, context=None):
        """ Paybox URLS """
        url = acquirer['paybox_url']
        url += self.paiement_cgi

        return {
            'paybox_form_url': url
        }

    def paybox_get_form_action_url(self, cr, uid, id, context=None):
        acquirer = self.browse(cr, uid, id, context=context)
        return self._get_paybox_urls(cr, uid, acquirer, context=context)['paybox_form_url']
