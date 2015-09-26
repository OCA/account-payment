# coding: utf-8
import urllib
import base64
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA


class Signature():

    def verify(self, signature, msg, key):
        """ check if the signature is correct according to the public key path given
            and the message """
        msg = self.remove_sign(msg)
        key = RSA.importKey(key)
        ha = SHA.SHA1Hash().new(msg)
        verifier = PKCS1_v1_5.new(key)
        signature = urllib.unquote(signature)
        signature = base64.b64decode(signature)
        return verifier.verify(ha, signature)

    def remove_sign(self, msg):
        """ remove signature arg from the given string"""
        pos = msg.find('&Signature')
        if pos == -1:
            return msg
        return msg[:pos]
