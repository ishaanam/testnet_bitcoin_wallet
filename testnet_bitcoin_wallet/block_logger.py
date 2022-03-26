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
from segwit import decode_bech32

try:
    # if possible, import the HOST variable from network_settings.py
    from network_settings import HOST
except (ModuleNotFoundError, ImportError):
    # otherwise, create network_settings.py and set the HOST variable to the default node
    with open("network_settings.py", "w") as net_file:
        HOST = "testnet.programmingbitcoin.com"
        net_file.write(f"HOST = {HOST}")

logging.basicConfig(filename='block.log', format='%(levelname)s:%(message)s', level=logging.DEBUG)

def block_syncer():
    node = SimpleNode(HOST, testnet=True, logging=False)
    node.handshake()
    # As long as wallet is running
    while True:
        now_hash = get_latest_block_hash()
        then_hash = read_log(-1)
        current_addr = get_all_addr()
        bf = BloomFilter(size=30, function_count=5, tweak=1729)
        # if a new block has been mined 
        if now_hash != then_hash:
            for addr in current_addr:
                prefix = addr[0]
                if prefix == "n" or prefix == "m":
                    h160 = decode_base58(addr)
                elif prefix == "t":
                    h160 = decode_bech32(addr, testnet=True)
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
            signal.signal(signal.SIGALRM, handler)
            signal.alarm(40)
            # for 40 seconds, see if we recieve any relevant transactions
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
                            ids = get_all_ids()
                            # check for any transaction outputs pertaining to us
                            for i, tx_out in enumerate(message.tx_outs):
                                for addr in current_addr:
                                    if get_address(tx_out.script_pubkey) == addr:
                                        prev_tx = message.hash().hex()
                                        prev_index = i
                                        prev_amount = tx_out.amount
                                        r_user = find_user(addr)
                                        locking_script = tx_out.script_pubkey
                                        block = get_block_hex(merkle_block)
                                        # set the transaction as confirmed in the corresponding user's file
                                        tx_set_confirmed(r_user, prev_tx, prev_index, prev_amount, addr, locking_script, block)
                                        logging.info(f"{r_user} recieved {prev_amount} satoshis")
                            # check for any transaction inputs indicating we have spent funds
                            for i, tx_in in enumerate(message.tx_ins):
                                for tx_id in ids:
                                    if tx_id[0] == tx_in.prev_tx.hex() and int(tx_id[1]) == tx_in.prev_index:
                                        tx_set_flag(tx_id[2], tx_id[0], '3', tx_id[1])
                    except SyntaxError:
                        logging.info("recieved an invalid script")
            except RuntimeError:
                pass

        # wait for ten seconds before checking if more blocks have been mined
        time.sleep(10)

