from ProgrammingBitcoin.tx import Tx
from ProgrammingBitcoin.script import Script

from bech32 import decode

# Makes both p2wpkh and p2wsh scripts
# TO-DO: `h160` isn't always 160 bits, in the case of p2wsh it should actually be 256 bits, so the name should be changed
def make_p2wx_script(h160):
    return Script([0x00, h160])

def decode_bech32(addr, testnet=False):
    if testnet:
        hrp = "tb"
    else:
        hrp = "bc"
    version, decoded = decode(hrp, addr)
    if version == None:
        raise ValueError("invalid address")
    return(bytes.__new__(bytes, decoded), version)

class SegwitTx(Tx):
    def __init__(self, version, tx_ins, tx_outs, witness, locktime, testnet=False):
        super().__init__(version, tx_ins, tx_outs, locktime, testnet)
        self.marker = b'\x00'
        self.flag = b'\x01' 
        self.witness = witness

    def segwit_serialize(self):
        pass

    def wtxid(self):
        pass
    
    def sig_hash(self):
        pass
