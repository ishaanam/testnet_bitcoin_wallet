from ProgrammingBitcoin.network import (
    GetDataMessage,
    GetHeadersMessage,
    HeadersMessage,
    NetworkEnvelope,
    SimpleNode,
    TX_DATA_TYPE,
    FILTERED_BLOCK_DATA_TYPE,
)

from hd import HD_Key
from jbok import get_addr

from ProgrammingBitcoin.block import Block 
from ProgrammingBitcoin.bloomfilter import BloomFilter 
from ProgrammingBitcoin.ecc import PrivateKey
from ProgrammingBitcoin.helper import hash256, little_endian_to_int, encode_varint, read_varint, decode_base58, SIGHASH_ALL
from ProgrammingBitcoin.merkleblock import MerkleBlock
from ProgrammingBitcoin.script import p2pkh_script, Script
from ProgrammingBitcoin.tx import Tx, TxIn, TxOut

from block_utils import *

from math import ceil
import csv
import time
import signal
from numpy import array, array_split

TESTNET_GENESIS_BLOCK = bytes.fromhex("000000000933ea01ad0ee984209779baaec3ced90fa3f408719526f8d77f4943")
WALLET_START_BLOCK = bytes.fromhex("0000000062043fb2e5091e43476e485ddc5d726339fd12bb010d5aeaf2be8206")

try:
    from network_settings import HOST
except (ModuleNotFoundError, ImportError):
    with open("network_settings.py", "w") as net_file:
        net_file.write('HOST = "testnet.programmingbitcoin.com"')
        HOST = 'testnet.programmingbitcoin.com'

def get_start_blocks(height):
    latest_height = get_known_height() 
    start_blocks = []
    with open("block_log.csv") as block_file:
        r = csv.reader(block_file)
        blocks = list(r)
    for i, block in enumerate(blocks):
        if int(block[1]) == height:
            blocks = blocks[(i-10):]
            break
    for i, block in enumerate(blocks):
        if i%2000 == 0:
            start_blocks.append(block[0])
    return start_blocks

def get_birthday_hash(word):
    start_block = 2164464
    with open("english.txt", 'r') as words:
        for i, w in enumerate(words):
            if w[:-1] == word:
                break
    h = (i*144) + start_block
    block_hash = get_hash_from_height(h)
    return block_hash, h

def generate_batch(key, index):
    current_addr = []
    for _ in range(40):
        ck = key.CKDpriv(index).k
        addr = get_addr(ck)
        current_addr.append([ck, addr])
        index += 1
    return current_addr, index 

def gap_exceeded(username, current_addr):
    with open(f"{username}_utxos.csv", 'r') as utxos:
        r = csv.reader(utxos)
        lines = list(r)
    latest_addr = lines[-1][3]
    for i, line in enumerate(current_addr):
        if line[1] == latest_addr:
            break
    print(i)
    print(39 - i)
    print(latest_addr)
    if (39 - i)> 20:
        print("returning False")
        return False, latest_addr
    else:
        return True, ""

def recover_batch(r_user, node, current_addr, height):
    utxos = []
    start_blocks = get_start_blocks(height)
    bf = BloomFilter(size=30, function_count=5, tweak=1729)
    for addr in current_addr:
        h160 = decode_base58(addr[1])
        bf.add(h160)
    for start in start_blocks:
        start_block = bytes.fromhex(start)
        node.send(bf.filterload())
        getheaders = GetHeadersMessage(start_block=start_block)
        node.send(getheaders)
        headers = node.wait_for(HeadersMessage)
        getdata = GetDataMessage()
        
        for block in headers.blocks:
            if not block.check_pow():
                raise RuntimeError('pow is invalid')
            getdata.add_data(FILTERED_BLOCK_DATA_TYPE, block.hash())
        node.send(getdata)
        signal.signal(signal.SIGALRM, handler)
        signal.alarm(40)
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
                        for i, tx_out in enumerate(message.tx_outs):
                            for addr in current_addr:
                                addr = addr[1]
                                if tx_out.script_pubkey.address(testnet=True) == addr:
                                    prev_tx = message.hash().hex()
                                    prev_index = i
                                    prev_amount = tx_out.amount
                                    locking_script = tx_out.script_pubkey
                                    block = get_block_hex(merkle_block)
                                    tx_set_confirmed(r_user, prev_tx, prev_index, prev_amount, addr, locking_script, block)
                                    logging.info(f"{r_user} recieved {prev_amount} satoshis")
                        for i, tx_in in enumerate(message.tx_ins):
                            for tx_id in ids:
                                if tx_id[0] == tx_in.prev_tx.hex() and int(tx_id[1]) == tx_in.prev_index:
                                    tx_set_flag(tx_id[2], tx_id[0], '3', tx_id[1])
                except SyntaxError:
                    pass
        except RuntimeError as e:
            pass
        incomplete, latest_addr = gap_exceeded(r_user, current_addr)
        print(f"Returning {incomplete}")
        return incomplete, latest_addr 
        
def recover_funds(username, last_words=None):
    if last_words == None:
        last_words = ['abandon', 'abandon']
    with open('users.csv', 'r') as user_file:
        r = csv.reader(user_file)
        users = list(r)
    for user in users:
        if user[0] == username:
            tprv = user[2]
    key = HD_Key.parse_priv(tprv) 
    index = 0
    all_addr = []
    
    if last_words:
        birthday_word = last_words[1]
        birthday, birthday_height = get_birthday_hash(birthday_word)
        if birthday == None:
            print("You must let your wallet sync further in order to be able to recover all addresses, please try again once your wallet has fully synchronized with the blockchain. (Use 'status' in order to check when the wallet is synced)")
        if last_words[0] == "abandon":
            # generate and check for legacy addresses 
            incomplete = True
            node = SimpleNode(HOST, testnet=True, logging=False)
            node.handshake()
            while incomplete:
                current_addr, index = generate_batch(key, index)
                all_addr += current_addr
                incomplete, last_addr = recover_batch(username, node, current_addr, birthday_height)
            for i, addr in enumerate(all_addr):
                if addr[1] == last_addr:
                    break
            all_addr = all_addr[:i+5]
            with open(f"{username}.csv", 'w', newline="") as addr_file:
                w = csv.writer(addr_file)
                w.writerows(all_addr)
        if last_words[0] == "ability":
            # generate and check for segwit addresses
            pass
    else:
        # generate and check both legacy & segwit
        # and use the software's birthday as the wallet birthday
        pass
