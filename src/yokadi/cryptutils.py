# coding:utf-8
"""
Cryptographic functions for encrypting and decrypting text.
Temporary file are used by only contains encrypted data.

@author: Sébastien Renard <Sebastien.Renard@digitalfox.org>
@license: GPL v3
"""

import base64
import hashlib
from random import Random

import tui
import db

from sqlobject import SQLObjectNotFound

# Prefix used to recognise encrypted message
CRYPTO_PREFIX = "---YOKADI-ENCRYPTED-MESSAGE---"
# AES Key length
KEY_LENGTH = 32

try:
    from Crypto.Cipher import AES as Cypher
    CRYPT = True
except ImportError:
    tui.warning("Python Cryptographic Toolkit module not found. You will not be able to use cryptographic function")
    tui.warning("like encrypting or decrypting task title or description")
    tui.warning("You can find pycrypto here http://www.pycrypto.org")
    CRYPT = False

#TODO: add unit test

class YokadiCryptoManager(object):
    """Manager object for Yokadi cryptographic operation"""
    def __init__(self):
        self.passphrase = None # Cache encryption passphrase
        try:
            self.crypto_check = db.Config.byName("CRYPTO_CHECK").value
        except SQLObjectNotFound:
            # Ok, set it to None. It will be setup after user defined passphrase
            self.crypto_check = None



    def encrypt(self, data):
        """Encrypt user data.
        @return: encrypted data"""
        if not CRYPT:
            tui.warning("Crypto functions not available")
            return data
        self.askPassphrase()
        return self._encrypt(data)


    def _encrypt(self, data):
        """Low level encryption interface. For internal usage only"""
        data = adjustString(data, KEY_LENGTH) # Complete data with blanck
        cypher = Cypher.new(self.passphrase)
        return CRYPTO_PREFIX + base64.b64encode(cypher.encrypt(data))

    def decrypt(self, data):
        """Decrypt user data.
        @return: decrypted data"""
        if not CRYPT:
            tui.warning("Crypto functions not available")
            return data
        data = data[len(CRYPTO_PREFIX):] # Remove crypto prefix
        data = base64.b64decode(data)
        self.askPassphrase()
        if self.passphrase:
            cypher = Cypher.new(self.passphrase)
            data = cypher.decrypt(data).rstrip()
        else:
            data = "<...Failed to decrypt data...>"
        return data


    def askPassphrase(self):
        """Ask user for passphrase if needed"""
        delay = int(db.Config.byName("PURGE_DELAY").value)
        cache = bool(int(db.Config.byName("PASSPHRASE_CACHE").value))
        if self.passphrase and cache:
            return
        self.passphrase = tui.editLine("", prompt="passphrase> ", echo=False)
        self.passphrase = adjustString(self.passphrase, KEY_LENGTH)

        if not self.isPassphraseValid() and cache:
            tui.warning("Passphrase differ from previous one."
                        "If you really want to change passphrase, "
                        "you should blank the  CRYPTO_CHEKC parameter"
                        "with c_set CRYPTO_CHECK '' "
                        "Note that you won't be able to retrieve previous tasks you"
                        "encrypted with your lost passphrase")
            self.passphrase = None

    def isEncrypted(self, data):
        """Check if data is encrypted
        @return: True is the data seems encrypted, else False"""
        if data.startswith(CRYPTO_PREFIX):
            return True
        else:
            return False

    def isPassphraseValid(self):
        """Check if user passphrase is valid.
        ie. : if it can decrypt the check crypto word"""
        if self.crypto_check:
            try:
                cypher = Cypher.new(self.passphrase)
                int(cypher.decrypt(self.crypto_check))
                return True
            except ValueError:
                return False
        else:
            # First time that user enter a passphrase. Store the crypto check 
            # for next time usage
            # We use a long string composed of int that we encrypt
            check_word = str(Random().getrandbits(KEY_LENGTH * KEY_LENGTH))
            check_word = adjustString(check_word, 10 * KEY_LENGTH)
            self.crypto_check = self._encrypt(check_word)

            # Save it to database config 
            db.Config(name="CRYPTO_CHECK", value=self.crypto_check, system=True,
                      desc="Cryptographic check data of passphrase")
            return True


def adjustString(string, length):
    """Adjust string to meet cipher requirement length"""
    string = string[:length] # Shrink if key is too large
    string = string.ljust(length, " ") # Complete if too short
    return string
