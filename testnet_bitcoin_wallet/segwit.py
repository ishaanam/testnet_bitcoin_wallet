from tx import Tx, TxIn, TxOut

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

class SegwitTxIn(TxIn):
    def __init__(self, prev_tx, prev_index, script_sig=None, sequence=0xff):
        pass

class SegwitTxOut(TxOut):
    def __init__(self,amount, script_pubkey):
        pass
