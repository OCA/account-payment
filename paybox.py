# coding: utf-8
from openerp.osv import osv, fields
import binascii
import hashlib
import logging
from datetime import datetime
from openerp.tools.translate import _
from openerp.tools import float_repr
import urllib
from openerp.addons.payment.models.payment_acquirer import ValidationError
from openerp.tools.float_utils import float_compare
from paybox_signature import Signature
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
            'key': '0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF',
            'shop_id': '107904482',
            'rank': '32',
            'site': '1999888',
            'hash': 'SHA512',
            'url': 'https://preprod-tpeweb.paybox.com/',
            'method': 'POST',
            'devise': '978',
         }

    def _get_providers(self, cr, uid, context=None):
        providers = super(PayboxAcquirer, self)._get_providers(cr, uid, context=context)
        providers.append(['paybox', 'Paybox'])
        return providers

    def build_paybox_args(self, cr, uid, acquirer, tx_values, context=None):
        reference = tx_values['reference']
        amount = tx_values['amount']
        key = acquirer['paybox_key']
        identifiant, devise = acquirer['paybox_shop_id'], acquirer['paybox_currency']
        rang, site = acquirer['paybox_rank'], acquirer['paybox_site']
        _hash = acquirer['paybox_hash']
        porteur = tx_values['partner'].email
        url = acquirer['paybox_url']
        url += self.paiement_cgi
        url_retour = acquirer['paybox_return_url']

        if not url_retour:
            raise osv.except_osv(u"Paiement impossible", u"URL de retour non configurée")

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

class PaymentTxPaybox(osv.Model):
    _inherit = 'payment.transaction'

    sign = Signature()
    pubkey = 'http://www1.paybox.com/wp-content/uploads/2014/03/pubkey.pem'
    base_url = '#id=%s&view_type=form&model=account.invoice&menu_id=%s&action=%s'
    ERROR_SUCCESS = ['00000']
    ERROR_CODE = {
            '00001': u"La connexion au centre d'autorisation a échoué ou une erreur interne est survenue",
            '001': u"Paiement refusé par le centre d'autorisation", '00003': u"Erreur Paybox",
            '00004': u"Numéro de porteur ou cryptogramme visuel invalide",
            '00006': u"Accès refusé ou site/rang/identifiant incorrect",
            '00008': u"Date de fin de validité incorrecte", '00009': u"Erreur de création d'un abonnement",
            '00010': u"Devise inconnue", '00011': u"Montant incorrect", '00015': u"Paiement déjà effectué",
            '00016': u"Abonné déjà existant", '00021': u"Carte non autorisée",
            '00029': u"Carte non conforme",
            '00030': u"Temps d'attente supérieur à 15 minutes par l'acheteur au niveau la page de paiement",
            '00033': u"Code pays de l'adresse IP du navigateur de l'acheteur non autorisé",
            '00040': u"Opération sans authentification 3-D Secure, bloquée par le filtre",
            }
    AUTH_CODE = {
            '03': u"Commerçant invalide", '05': u"Ne pas honorer",
            '12': u"Transaction invalide", '13': u"Montant invalide",
            '14': u"Numéro de porteur invalide", '15': u"Emetteur de carte inconnu",
            '17': u"Annulation client", '19': u"Répéter la transaction ultérieurement",
            '20': u"Réponse erronée (erreur dans le domaine serveur)",
            '24': u"Mise à jour de fichier non supportée",
            '25': u"Impossible de localiser l'enregistrement dans le fichier",
            '26': u"Enregistrement dupliqué, ancien enregistrement remplacé",
            '27': u"Erreur en \"edit\" sur champ de mise à jour fichier",
            '28': u"Accès interdit au fichier", '29': u"Mise à jour de fichier impossible",
            '30': u"Erreur de format", '33': u"Carte expirée",
            '38': u"Nombre d'essais code confidentiel dépassé",
            '41': u"Carte perdue", '43': u"Carte volée", '51': u"Provision insuffisante ou crédit dépassé",
            '54': u"Date de validité de la carte dépassée", '55': u"Code confidentiel erroné",
            '56': u"Carte absente du fichier", '57': u"Transaction non permise à ce porteur",
            '58': u"Transaction interdite au terminal", '59': u"Suspicion de fraude",
            '60': u"L'accepteur de carte doit contacter l'acquéreur",
            '61': u"Dépasse la limite du montant de retrait",
            '63': u"Règles de sécurité non respectées",
            '68': u"Réponse non parvenue ou reçue trop tard",
            '75': u"Nombre d'essais code confidentiel dépassé",
            '76': u"Porteur déjà en opposition, ancien enregistrement conservé",
            '89': u"Echec de l'authentification", '90': u"Arrêt momentané du système",
            '91': u"Emetteur de carte inaccessible", '94': u"Demande dupliquée",
            '96': u"Mauvais fonctionnement du système",
            '97': u"Echéance de la temporisation de surveillance globale",
            }

    def build_args(self, args):
        if 'Auto' not in args:
            msg = 'Mt='+args['Mt']+'&Ref='+urllib.quote_plus(args['Ref'])
        else:
            msg = 'Mt='+args['Mt']+'&Ref='+urllib.quote_plus(args['Ref'])+'&Auto='+args['Auto']
        msg += '&Erreur='+args['Erreur']+'&Signature='+args['Signature']
        return msg

    def check_error_code(self, erreur):
        """ check if the error code is a real error or not.
            it also build the message that will be display to the customer """
        if erreur in self.ERROR_CODE:
            error_msg = self.ERROR_CODE[erreur]
            return error_msg
        else:
            for err in self.ERROR_CODE:
                if erreur.startswith(err):
                    error_msg = self.AUTH_CODE[erreur[-2:]]
                    return error_msg
        return False

    def _paybox_form_get_tx_from_data(self, cr, uid, data, context=None):
        for field in ('Erreur', 'Auto', 'Signature', 'Mt', 'Ref'):
            if field not in data:
                raise ValidationError(u"Paramètre %s non trouvé" % repr(field))

        ref = data['Ref']
        tx_ids = self.search(cr, uid, [('reference', '=', ref)], context=context)
        error_msg = 'Paybox: received data for reference %s' % ref

        if not tx_ids:
            error_msg += '; no transaction found'
            raise ValidationError(error_msg)

        if len(tx_ids) > 1:
            error_msg += '; multiple transactions found'
            raise ValidationError(error_msg)

        tx = self.pool['payment.transaction'].browse(cr, uid, tx_ids[0], context=context)
        key = urllib.urlopen(self.pubkey).read()
        signature = data['Signature']

        msg = self.build_args(data)
        if not self.sign.verify(signature, msg, key):
            raise ValidationError(u"Signature non vérifiée")

        return tx

    def _paybox_form_get_invalid_parameters(self, cr, uid, tx, data, context=None):
        invalid_parameters = []

        # TODO: txn_id: should be false at draft, set afterwards, and verified with txn details
        if tx.acquirer_reference and data.get('Ref') != tx.acquirer_reference:
            invalid_parameters.append(('Ref', data.get('Ref'), tx.acquirer_reference))

        actualAmount = float(data['Mt'])/100
        if float_compare(actualAmount, tx.amount, 2) != 0:
            invalid_parameters.append(('Mt', actualAmount, '%.2f' % tx.amount))

        return invalid_parameters

    def _paybox_form_validate(self, cr, uid, tx, data, context=None):
        if tx.state == 'done':
            _logger.warning('Paybox: trying to validate an already validated tx (ref %s)' % tx.reference)
            return True

        ref = data['Ref']
        montant = data['Mt']

        error_code = data['Erreur']
        error_msg = self.check_error_code(error_code)

        if error_msg:
            error = u'Erreur Paybox [%s] %s' % (error_code, error_msg)
            _logger.info(error)
            tx.write({
                'state': 'error',
                'state_message': error,
                'acquirer_reference': ref,
            })
            return False

        if ref and montant and error_code in self.ERROR_SUCCESS:
            tx.write({
                'state': 'done',
                #'date_validate': data['TRXDATE'],
                'acquirer_reference': ref
            })
            return True

        tx.write({
            'state': 'error',
            'state_message': "Erreur Paybox inconnue",
            'acquirer_reference': ref,
        })
        return False
