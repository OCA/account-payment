# coding: utf-8
from openerp.osv import osv
import logging
import urllib
from openerp.addons.payment.models.payment_acquirer import ValidationError
from openerp.tools.float_utils import float_compare
import util

_logger = logging.getLogger(__name__)

class PaymentTxPaybox(osv.Model):
    _inherit = 'payment.transaction'

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
        if not util.verify(signature, msg, key):
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
