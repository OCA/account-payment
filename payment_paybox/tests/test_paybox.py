# coding: utf-8

import os
from openerp.tests.common import TransactionCase
from openerp.osv import osv
from ..controllers.main import PayboxController
from ..models import util

class TestPaybox(TransactionCase):

    def setUp(self):
        super(TestPaybox, self).setUp()
        self.acquirer = self.registry('payment.acquirer')
        self.journal = self.registry('account.journal')
        self.account = self.registry('account.account')
        self.partner = self.registry('res.partner')
        self.product = self.registry('product.product')
        self.mail = self.registry('mail.mail')
        self.controller = PayboxController()
        self.company_id = 1
        self.currency_id = 1
        self.product_id = self.product.search(
            self.cr, self.uid, [])[0]
        self.product_name = self.product.browse(self.cr, self.uid, self.product_id).name
        self.product_account_id = self.account.search(
            self.cr, self.uid, [('code', '=', '707100')])[0]

    def test_check_error_code(self):
        """ ensure the check_error_code() method return the appropriate message """
        check = self.controller.check_error_code('00029')
        self.assertEquals(check, u"Carte non conforme")
        check = self.controller.check_error_code('00115')
        self.assertEquals(check, u"Emetteur de carte inconnu")
        check = self.controller.check_error_code('00000')
        self.assertFalse(check)

    def test_remove_sign(self):
        msg = 'db=test_db&Mt=35000&Ref=SAJ/000/000&Auto=XXXXXX&Erreur=00000'
        clean_msg = util.remove_sign(msg)
        self.assertEquals(clean_msg, msg)
        msg = 'db=test_db&Mt=35000&Ref=SAJ/000/000&Auto=XXXXXX&Erreur=00000&Signature=DmqslqAeazsqd'
        clean_msg = util.remove_sign(msg)
        self.assertEquals(clean_msg, 'db=test_db&Mt=35000&Ref=SAJ/000/000&Auto=XXXXXX&Erreur=00000')

    def test_compute_hmac(self):
        """ ensure that the hmac is well computed """
        key = '0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF'
        args = 'PBX_SITE=1999888&PBX_RANG=32&PBX_HASH=SHA512&PBX_CMD=SAJ/2014/8503&PBX_IDENTIFIANT=110647233&PBX_TOTAL=150.0&PBX_DEVISE=978&PBX_PORTEUR=test@paybox.com&PBX_RETOUR=Mt:M;Ref:R;Auto:A;Erreur:E&PBX_TIME=2014-09-29 10:26:17.542412'
        hash_name = 'SHA512'
        hmac = self.acquirer.compute_hmac(key, hash_name, args)
        self.assertEquals(hmac, '77C0800DF057BC78AA59879DE918168F59759A5F876B00447ABF5C7555A30BF1AFE0ACAD7D33B33415225AA4B5749005F89A05F130CF6D8D7677B77D1DB35A80')
        hash_128 = 'SHA128'
        self.assertRaises(osv.except_osv, self.acquirer.compute_hmac, key, hash_128, args)

    def test_verify_signature(self):
        """ verify the signature according to datas and public key """
        path = os.path.dirname(os.path.abspath(__file__))
        key_path = path+'/pubkey.pem'
        sign_path = path+'/sig64.txt'
        data_path = path+'/data.txt'
        signature = open(sign_path, 'r').read()
        data = open(data_path, 'r').read()
        key = open(key_path, 'r').read()
        res = util.verify(signature, data, key)
        self.assertTrue(res)
        res = util.verify(signature, data.replace('Mt=35000', 'Mt=50000'), key)
        self.assertFalse(res)
