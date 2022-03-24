from mnemonic import Mnemonic
from ProgrammingBitcoin.ecc import PrivateKey
from ProgrammingBitcoin.helper import hash160, encode_base58_checksum
from block_utils import read_log, get_height 
import hashlib
import hmac
import getpass
import base58
import math

num = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141

def get_birthday():
    # storing the wallet birthday in this manner will work for around 5.6 years before we run out of words
    start_block = 2164464
    block = read_log(-1)
    h = get_height('block_log.csv', block)
    h -= start_block
    n = math.floor(h/144) 
    with open("english.txt", "r") as words:
        for i, line in enumerate(words):
            if i == n:
                birthday_word = line
                break
    if birthday_word:
        return birthday_word[:-1]

def new_mnemonic(v=-1):
    mnemo = Mnemonic('english')
    words = mnemo.generate(strength=128)
    if v == 0: 
        version_word = "ability"
    elif v == -1:
        version_word = "abandon"
    new_words = words +  f" {version_word}" 
    new_words += f" {get_birthday()}" 
    print(new_words)
    passphrase = getpass.getpass(prompt="Passphrase(if none just enter): ")
    seed = mnemo.to_seed(words, passphrase=passphrase)
    return seed

class HD_Key(PrivateKey):
    def __init__(self, level, fingerprint, index, k, c, testnet=False):
        super().__init__(int(k, 16))
        self.level = level
        self.fingerprint = fingerprint
        self.index = index
        self.k = k
        self.c = c
        self.testnet = testnet
    
    def __repr__(self):
        return(f"level: {self.level}, fingerprint: {self.fingerprint}, index: {self.index}, k: {self.k}, c: {self.c}, testnet: {self.testnet}")

    @classmethod
    def new_master_key(cls, level, fingerprint,index, seed, testnet=False):
        i = hmac.new(b"Bitcoin seed", seed, hashlib.sha512).digest()
        key = i[:32]
        chain = i[32:]
        if (int.from_bytes(key, 'big') == 0) or (int.from_bytes(key, 'big') >= num):
            print("invalid key generated")
            return None
        else:
            return cls(level, fingerprint, index, key.hex(), chain.hex(), testnet)
    
    def get_fingerprint(self):
        K = self.point.sec(compressed=True)
        h160 = hash160(K)
        return h160.hex()[:8]

    def CKDpriv(self, index):
        no_key = True
        while no_key:
            key = bytes.fromhex(self.c) 
            K = self.point.sec(compressed=True)
            data = K + index.to_bytes(4, 'big')
            I = hmac.new(key, data, hashlib.sha512).digest()
            L = I[:32]
            R = I[32:]
            ck = (int.from_bytes(L, 'big') + int(self.k, 16)) % num
            cc = R
            c_level = int(self.level) + 1
            c_fingerprint = self.get_fingerprint()
            if ck == 0 or int(L.hex(), 16) >= num:
                index += 1
            else:
                return HD_Key(str(c_level).zfill(2), c_fingerprint, hex(index)[2:].zfill(8), hex(ck)[2:], cc.hex())

    def serialize(self, priv=False):
        if priv:
            if self.testnet:
                s = bytes.fromhex("04358394")
            else:
                s = bytes.fromhex("0488ADE4")
            k = bytes.fromhex("00")
            k += bytes.fromhex(self.k)
        else:
            if self.testnet:
                s = bytes.fromhex("043587CF")
            else:
                s = bytes.fromhex("0488B21E")
            k = self.point.sec(compressed=True)
        s += bytes.fromhex(self.level)
        s += bytes.fromhex(self.fingerprint)
        s += bytes.fromhex(self.index)
        s += bytes.fromhex(self.c)
        s += k
        return(encode_base58_checksum(s))


    @classmethod
    def parse_priv(cls, s):
        version = s[:4]
        if version == "xprv":
            testnet = False
        elif version == "tprv":
            testnet = True
        else:
            print("invalid private key serialization")
            return None
        s = base58.b58decode(s).hex()
        s = s[8:]
        level = s[:2]
        fingerprint = s[2:10]
        index = s[10:18]
        c = s[18:82]
        k = s[84:148]
        return cls(level, fingerprint, index, k, c, testnet)

    @staticmethod
    def recover_wallet(words):
        mnemo = Mnemonic('english')
        passphrase = getpass.getpass(prompt="Passphrase(if none just enter): ")
        seed = mnemo.to_seed(words, passphrase=passphrase)
        key = HD_Key.new_master_key("00", "00000000", "00000000", seed, testnet=True)
        return key.serialize(priv=True)
    
    @staticmethod
    def new_tprv(v):
        seed = new_mnemonic(v)
        tprv = HD_Key.new_master_key("00", "00000000", "00000000", seed, testnet=True)
        return tprv.serialize(priv=True) 

