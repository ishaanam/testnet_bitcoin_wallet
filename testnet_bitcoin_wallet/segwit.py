import unittest 

from ProgrammingBitcoin.tx import Tx, TxIn, TxOut
from ProgrammingBitcoin.script import Script
from ProgrammingBitcoin.helper import (
    encode_varint,
    hash256,
    int_to_little_endian,
    little_endian_to_int,
    read_varint,
    SIGHASH_ALL,
)

from bech32 import decode, encode

def make_p2wpkh_script(h160):
    return Script([0x00, h160])

def decode_bech32(addr, testnet=False):
    if testnet:
        hrp = "tb"
    else:
        hrp = "bc"
    version, decoded = decode(hrp, addr)
    if version == None:
        raise ValueError("invalid address")
    return(bytes.__new__(bytes, decoded))

def make_p2wpkh_address(h160):
    hrp = "tb"
    witver = 0
    return encode(hrp, witver, h160)

class SegwitTx(Tx):
    def __init__(self, version, marker, flag, tx_ins, tx_outs, locktime, testnet=False):
        super().__init__(version, tx_ins, tx_outs, locktime, testnet)
        self.marker = marker 
        self.flag = flag 

    def serialize_segwit(self):
        result = int_to_little_endian(self.version, 4)
        result += self.marker
        result += self.flag
        result += encode_varint(len(self.tx_ins))
        for tx_in in self.tx_ins:
            result += tx_in.serialize()
        result += encode_varint(len(self.tx_outs))
        for tx_out in self.tx_outs:
            result += tx_out.serialize()
        for tx_in in self.tx_ins:
            result += tx_in.witness.serialize()
        result += int_to_little_endian(self.locktime, 4)
        return result

    @classmethod
    def parse(cls, s):
        version = little_endian_to_int(s.read(4))
        marker = s.read(1)
        flag = s.read(1)
        # num_inputs is a varint, use read_varint(s) 
        num_inputs = read_varint(s)
        # parse num_inputs number of TxIns
        inputs = []
        for _ in range(num_inputs):
            inputs.append(TxIn.parse(s))
        # num_outputs is a varint, use read_varint(s)
        num_outputs = read_varint(s)
        # parse num_outputs number of TxOuts
        outputs = []
        for _ in range(num_outputs):
            outputs.append(TxOut.parse(s))
        # locktime is an integer in 4 bytes, little-endian
        for tx_in in inputs:
            tx_in.witness = Witness.parse(s)
        locktime = little_endian_to_int(s.read(4))
        return cls(version, marker, flag,inputs, outputs, locktime)

    def sig_hash_segwit_v0(self, input_index): 
        pass

class Witness():
    def __init__(self, items):
        self.items = items
    
    def serialize(self):
        result = encode_varint(len(self.items))
        for item in self.items:
            if len(item) == 1:
                result += item
            else:
                result += encode_varint(len(item)) + item
        return result

    @classmethod
    def parse(cls, s):
        num_items = read_varint(s)
        items = []
        for _ in range(num_items):
            item_size = read_varint(s)
            items.append(s.read(item_size))
        return cls(items)
