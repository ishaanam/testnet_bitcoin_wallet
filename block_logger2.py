from ProgrammingBitcoin.block import Block 
from ProgrammingBitcoin.bloomfilter import BloomFilter 
from ProgrammingBitcoin.ecc import PrivateKey
from ProgrammingBitcoin.helper import hash256, little_endian_to_int, encode_varint, read_varint, decode_base58, SIGHASH_ALL
from ProgrammingBitcoin.merkleblock import MerkleBlock
from ProgrammingBitcoin.network import (
    GetDataMessage,
    GetHeadersMessage,
    HeadersMessage,
    NetworkEnvelope,
    SimpleNode,
    TX_DATA_TYPE,
    FILTERED_BLOCK_DATA_TYPE,
)
from ProgrammingBitcoin.script import p2pkh_script, Script
from ProgrammingBitcoin.tx import Tx, TxIn, TxOut

from block_utils import start_log, get_latest_block_hash, get_all_users, get_all_addr, find_user, handler, get_block_hex, read_log,all_hashes, prev_fork_hash, get_forks, make_fork_file, write_block, reorg, need_reorg, tx_set_confirmed, tx_set_flag 

import csv
import time
import signal
import logging

try:
    from network_settings import HOST
except (ModuleNotFoundError, ImportError):
    with open("network_settings.py", "w") as net_file:
        net_file.write('HOST = "testnet.programmingbitcoin.com"')
        HOST = 'testnet.programmingbitcoin.com'

logging.basicConfig(filename='block.log', format='%(levelname)s:%(message)s', level=logging.DEBUG)

def block_syncer():
    node = SimpleNode(HOST, testnet=True, logging=False)
    node.handshake()
    #Actually "forever"
    while True:
        now_hash = get_latest_block_hash()
        try:
            then_hash = read_log(-1)
        except FileNotFoundError:
            then_hash = start_log()
        current_addr = get_all_addr()
        bf = BloomFilter(size=30, function_count=5, tweak=1729)
        # when a new block is recieved:
        if now_hash != then_hash:
            for addr in current_addr:
                h160 = decode_base58(addr)
                bf.add(h160)
            node.send(bf.filterload())
            start_block = bytes.fromhex(then_hash)
            getheaders = GetHeadersMessage(start_block=start_block)
            node.send(getheaders)
            headers = node.wait_for(HeadersMessage)
            getdata = GetDataMessage()

            for block in headers.blocks:
                if not block.check_pow():
                    raise RuntimeError('pow is invalid')
                logging.info(f"recieved block: {block.hash().hex()}")
                getdata.add_data(FILTERED_BLOCK_DATA_TYPE, block.hash())
                all_blocks = all_hashes()
                if block.hash().hex() in all_blocks:
                    pass
                else:
                    write_block(block.prev_block.hex(), block.hash().hex())
                reorg_file = need_reorg()
                if reorg_file != None:
                    reorg(reorg_file)
            node.send(getdata)
            # SET SIGNAL ALARM
            signal.signal(signal.SIGALRM, handler)
            signal.alarm(40)
            try:
                while True:
                    try:
                        message = node.wait_for(MerkleBlock, Tx)
                        if message.command == b'merkleblock':
                            merkle_block = message
                            if not message.is_valid():
                                raise RuntimeError('inalid merkle proof')
                        else:
                            message.testnet = True
                            for i, tx_out in enumerate(message.tx_outs):
                                for addr in current_addr:
                                    if tx_out.script_pubkey.address(testnet=True) == addr:
                                        prev_tx = message.hash().hex()
                                        prev_index = i
                                        prev_amount = tx_out.amount
                                        r_user = find_user(addr)
                                        locking_script = tx_out.script_pubkey
                                        block = get_block_hex(merkle_block)
                                        tx_set_confirmed(r_user, prev_tx, prev_index, prev_amount, addr, locking_script, block)
                                        logging.info(f"{r_user} recieved {prev_amount} satoshis")
                    except SyntaxError:
                        logging.info("recieved an invalid script")
            except RuntimeError:
                pass

        time.sleep(10)

""" Part #1: Block Syncing """
# KEY: keep all headers
# KEY: first block hash on fork files is the sme as the mian chain
"""
start_block = WALLET_GENESIS

when block is recieved:
    if: block builds on main chain:
        main += block
    else: for fork in forks:
        get_prev_hash()
        if prev_hash == message.prev_hash:
            # if no exsisting file for this fork, make a new one
            fork += block

    if the length of the forks is greater than the main chain lengths:
        switch files
"""

### "*_utxos.csv" format:
    # tx_id, index, amount, address, scriptPubKey, block_hash, confirmation_status 

""" set all flags belonging to tx mined in the blocks that were reorged out as unconfirmed 
    save these transactions as a dictionary 
    search for the txs within the x new blocks see if any of the txs were confirmed: 
    pop confirmed transactions from dictionary 
    if dictionary isn't empty: 
    notify the user that they may have been double-spent

"""

""" Part #2: UTXO Syncing """

# KEY: don't delete utxos if you've "spent"
# FLAGS:
# 0 = unconfirmed unspent, 1 = confirmed unspent, 2 = unconfirmed spent, 3 = confirmed spent 

# 0 when expecting change
# 1 when we've recieved a utxo and have never spent it
# 2 when we have spent a utxo and haven't recieved the transaction from the blockchain where we have spent it
# 3 when we've spent it an have recieved confirmation that we've spent it

"""
when transaction is recieved:
    if ouput is ours:
        if on main chain:
            add everything as usual
        else:
            do nothing, we'll get them in case of a reorg
    if input is ours:
        find tx in users file an mark that transaction as spent
        
"""
