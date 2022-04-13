import unittest 

from ProgrammingBitcoin.tx import Tx, TxIn, TxOut
from ProgrammingBitcoin.script import Script, p2pkh_script
from ProgrammingBitcoin.helper import (
    encode_varint,
    hash256,
    int_to_little_endian,
    little_endian_to_int,
    read_varint,
    SIGHASH_ALL,
)

from bech32 import decode, encode
from jbok import get_pkobj

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
    def parse(cls, s, testnet=False):
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
        return cls(version, marker, flag,inputs, outputs, locktime, testnet)

    def sig_hash_segwit_v0(self, input_index, h160, amount): 
        """
        From BIP-143
        Double SHA256 of the serialization of:
         1. nVersion of the transaction (4-byte little endian)
            [SELF EXPLANATORY]
         
         2. hashPrevouts (32-byte hash)
            hash256(all:txid+index) 
         
         3. hashSequence (32-byte hash)
            hash256(all:sequence)
         
         4. outpoint (32-byte hash + 4-byte little endian) 
            input being spent: tx_id+index
             
         5. scriptCode of the input (serialized as scripts inside CTxOuts)
            0x1976a914{20-byte-pubkey-hash}88ac
         
         6. value of the output spent by this input (8-byte little endian)
            [SELF EXPLANATORY]
         
         7. nSequence of the input (4-byte little endian)
            sequence on input
         
         8. hashOutputs (32-byte hash)
            hash245(all:amount+script_pubkey) 
         
         9. nLocktime of the transaction (4-byte little endian)
            [SELF EXPLANATORY]

        10. sighash type of the signature (4-byte little endian)
            [SELF EXPLANATORY]
        """

        s = int_to_little_endian(self.version, 4) #1
        prevouts = b"" 
        sequences = b"" 
        for tx_in in self.tx_ins:
            prevouts += tx_in.prev_tx[::-1]
            prevouts += int_to_little_endian(tx_in.prev_index, 4)
            sequences += int_to_little_endian(tx_in.sequence, 4)
        s += hash256(prevouts) #2
        s += hash256(sequences) #3
       
        tx_in = self.tx_ins[input_index] #4
        s += tx_in.prev_tx[::-1] + int_to_little_endian(tx_in.prev_index, 4)

        s += p2pkh_script(h160).serialize() #5
        s += int_to_little_endian(amount, 8) # 6
        s += int_to_little_endian(tx_in.sequence, 4) # 7

        outputs = b"" #8
        for tx_out in self.tx_outs:
            outputs += tx_out.serialize()
        
        s += hash256(outputs)
        s += int_to_little_endian(self.locktime, 4) #9
        s += int_to_little_endian(SIGHASH_ALL, 4) # 10
        return int.from_bytes(hash256(s), 'big')
    

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
