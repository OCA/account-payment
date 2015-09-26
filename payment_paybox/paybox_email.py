# coding: utf-8

from openerp.osv import osv, fields
import logging

templates = {
    'invoice': 'Warning Invoice Paybox',
    'reconcile': 'Warning Reconcile Paybox'
    }

logger = logging.getLogger(__name__)


class PayboxWarningEmail(osv.Model):

    _name = 'paybox.warning'

    _columns = {'ref': fields.char('Invoice reference'),
                'amount': fields.char('Payment amount'),
                'warning': fields.char('Warning')}

    def get_paybox_admin(self, cr, uid, context=None):
        """ return the mail address of the paybox administrator """
        cfg_param = self.pool.get('ir.config_parameter')
        admin = cfg_param.search(cr, uid, [('key', '=', 'paybox.admin_mail')])
        if not admin:
            logger.warning(u"[Paybox] Le paramètre 'admin_mail' n'a pas été trouvé")
            return False
        admin_mail = cfg_param.browse(cr, uid, admin[0]).value
        return admin_mail

    def send_warning_mail(self, cr, uid, obj_id, name, context=None):
        """ send a warning email to the paybox administrator """
        template = self.pool.get('email.template')
        template_name = templates[name] if name in templates else False
        template_id = template.search(
            cr, uid, [('name', '=', template_name)]) if template_name else False
        if not template_id:
            logger.warning(u"""[Paybox] - Le template %s n'a pas été trouvé,
l'email n'a pas été envoyé""" % (template_name))
            return False
        self.pool.get('email.template').send_mail(
            cr, uid, template_id[0], obj_id, force_send=True, context=context)
