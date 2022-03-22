from ProgrammingBitcoin.tx import Tx
from ProgrammingBitcoin.script import Script

def make_p2wpkh_script(h160):
    return Script([0x00, h160])

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
