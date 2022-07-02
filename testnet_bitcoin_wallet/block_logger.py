import time
import signal
import logging

from ProgrammingBitcoin.bloomfilter import BloomFilter
from ProgrammingBitcoin.helper import decode_base58
from ProgrammingBitcoin.merkleblock import MerkleBlock
from ProgrammingBitcoin.network import (
    GetDataMessage,
    GetHeadersMessage,
    HeadersMessage,
    SimpleNode,
    FILTERED_BLOCK_DATA_TYPE,
)
from ProgrammingBitcoin.tx import Tx

from block_utils import *

HOST = get_node()

logging.basicConfig(filename='block.log', format='%(levelname)s:%(message)s', level=logging.DEBUG)

def initial_connect():
    node = SimpleNode(HOST, testnet=True, logging=False)
    node.handshake()

def get_blocks(node):
    now_hash = get_latest_block_hash()
    then_hash = read_log(-1)
    last_height = get_known_height()
    blocks_and_heights = {}
    current_addr = get_all_addr()
    bf = BloomFilter(size=30, function_count=5, tweak=1729)
    if now_hash != then_hash:
        if is_synched():
            users = get_all_users()
            for user in users:
                with open(f"{user}_utxos.csv", 'r') as utxo_file:
                    r = csv.reader(utxo_file)
                    utxos = list(r)
                    for utxo in utxos:
                        if utxo[6] == TXOState.UNCONFIRMED_STXO.value:
                            utxo[6] = TXOState.CONFIRMED_UTXO.value
                with open(f"{user}_utxos.csv", 'w') as utxo_file:
                    w = csv.writer(utxo_file)
                    w.writerows(utxos)
        for addr in current_addr:
            h160 = decode_base58(addr)
            bf.add(h160)
        node.send(bf.filterload())
        last_block = bytes.fromhex(then_hash)
        getheaders = GetHeadersMessage(start_block=last_block)
        node.send(getheaders)
        headers = node.wait_for(HeadersMessage)
        getdata = GetDataMessage()

        for i, block in enumerate(headers.blocks):
            if not block.check_pow():
                raise RuntimeError('pow is invalid')
            if block.prev_block != last_block:
                raise ChainBrokenError()
            logging.info(f"received block: {block.hash().hex()}")
            getdata.add_data(FILTERED_BLOCK_DATA_TYPE, block.hash())
            blocks_and_heights[block.hash().hex()] = last_height + i + 1

            last_block = block.hash()

        write_block(block.prev_block.hex(), block.hash().hex(), len(headers.blocks))
        return getdata, blocks_and_heights
    return False, blocks_and_heights

def block_syncer():
    node = SimpleNode(HOST, testnet=True, logging=False)
    node.handshake()
    # As long as wallet is running
    fork_block_height = 0
    just_reorged = False
    while True:
        current_addr = get_all_addr()
        while True:
            try:
                getdata, blocks_and_heights = get_blocks(node)
                if just_reorged:
                    restore_transaction_states(fork_block_height)
                break
            except ChainBrokenError as e:
                logging.error("chain broken")
                fork_block_height = reorg()
                just_reorged = True
        if getdata:
            node.send(getdata)
            signal.signal(signal.SIGALRM, handler)
            signal.alarm(40)
            # for 40 seconds, see if we receive any relevant transactions
            try:
                while True:
                    try:
                        message = node.wait_for(MerkleBlock, Tx)
                        if message.command == b'merkleblock':
                            merkle_block = message
                            if not message.is_valid():
                                raise RuntimeError('invalid merkle proof')
                        else:
                            message.testnet = True
                            ids = get_all_ids()
                            # check for any transaction outputs pertaining to us
                            for i, tx_out in enumerate(message.tx_outs):
                                for addr in current_addr:
                                    if tx_out.script_pubkey.address(testnet=True) == addr:
                                        prev_tx = message.hash().hex()
                                        prev_index = i
                                        prev_amount = tx_out.amount
                                        r_user = find_user(addr)
                                        locking_script = tx_out.script_pubkey
                                        block = get_block_hex(merkle_block)
                                        # set the transaction as confirmed in the corresponding user's file
                                        tx_set_confirmed(r_user, prev_tx, prev_index, prev_amount, addr, locking_script, block, blocks_and_heights[block])
                                        logging.info(f"{r_user} received {prev_amount} satoshis")
                            # check for any transaction inputs indicating we have spent funds
                            for i, tx_in in enumerate(message.tx_ins):
                                for tx_id in ids:
                                    if tx_id[0] == tx_in.prev_tx.hex() and int(tx_id[1]) == tx_in.prev_index:
                                        tx_set_flag(tx_id[2], tx_id[0], TXOState.CONFIRMED_STXO.value, tx_id[1])
                    except SyntaxError:
                        logging.info("received an invalid script")
            except RuntimeError:
                pass

        # wait for ten seconds before checking if more blocks have been mined
        time.sleep(10)

