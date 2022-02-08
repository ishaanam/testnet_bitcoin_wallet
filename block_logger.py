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

import csv
import time
import signal

try:
    from network_settings import HOST
except (ModuleNotFoundError, ImportError):
    with open("network_settings.py", "w") as net_file:
        net_file.write('HOST = "testnet.programmingbitcoin.com"')
        HOST = 'testnet.programmingbitcoin.com'

def read_log(block_number):
    start_block = "0000000062043fb2e5091e43476e485ddc5d726339fd12bb010d5aeaf2be8206"
    try:
        with open('block_log.csv', 'r') as log_file:
            r = csv.reader(log_file)
            lines = list(r)
            try:
                return lines[block_number][0]
            except IndexError:
                return start_block
    except FileNotFoundError:
        with open('block_log.csv', 'w', newline="") as log_file:
            w = csv.writer(log_file)
            w.writerow((start_block, 2135892))
            print("made file")
            return start_block

def get_latest_block_hash():
    node = SimpleNode(HOST, testnet=True, logging=False)
    node.handshake()
    start_block = bytes.fromhex(read_log(-2))

    getheaders = GetHeadersMessage(start_block=start_block)
    node.send(getheaders)

    headers = node.wait_for(HeadersMessage)
    last_block = None 
    getdata = GetDataMessage()

    for block in headers.blocks:
        if not block.check_pow():
            raise RuntimeError('pow is invalid')
        if last_block is not None and block.prev_block != last_block:
            raise RuntimeError('chain broken')
        getdata.add_data(FILTERED_BLOCK_DATA_TYPE, block.hash())
        last_block = block.hash()
    return last_block.hex()

def find_user(addr):
    with open('users.csv', 'r') as users_file:
        r = csv.reader(users_file)
        lines = list(r)
        for line in lines:
            user = line[0]
            with open(f'{user}.csv', 'r') as addr_file:
                r = csv.reader(addr_file)
                addrs = list(r)
                for a in addrs:
                    address = a[1]
                    if address == addr:
                        return user

def get_all_users():
    users = []
    with open('users.csv', 'r') as user_file:
        r = csv.reader(user_file)
        lines = list(r)
        for line in lines:
            users.append(line[0])
    return users

def get_all_addr():
    users = get_all_users()

    addresses = []
    for user in users:
        if user != "username":
            with open(f'{user}.csv', 'r') as users_file:
                r = csv.reader(users_file)
                lines = list(r)
                for line in lines:
                    addresses.append(line[1])
    return addresses

def handler(signum, frame):
    raise Exception("timed out")

def get_block_hex(m):
    block = Block(m.version, m.prev_block, m.merkle_root, m.timestamp, m.bits, m.nonce)
    return block.hash().hex()

def input_parser(current_addr, node):
    while True:
        try:
            message = node.wait_for(MerkleBlock, Tx)
            if message.command == b'merkleblock':
                merkle_block = message
                if not message.is_valid():
                    raise RuntimeError('invalid merkle proof')
            else:
                message.testnet = True
                for i, tx_out in enumerate(message.tx_outs):
                    for addr in current_addr:
                        if tx_out.script_pubkey.address(testnet=True) == addr:
                            prev_tx = message.hash()
                            prev_tx = prev_tx.hex()
                            prev_index = i
                            prev_amount = tx_out.amount
                            r_user = find_user(addr)
                            locking_script = tx_out.script_pubkey
                            block = get_block_hex(merkle_block)
                            is_unknown = True 
                            with open(f'{r_user}_utxos.csv', 'r') as utxo_file:
                                r = csv.reader(utxo_file)
                                utxos = list(r)
                                for i, utxo in enumerate(utxos):
                                    print(utxo[0])
                                    if utxo[0] == prev_tx:
                                        print("recieved confirmation for a previously unconfirmed transaction")
                                        utxos.pop(i)
                            if is_unknown:
                                    utxos.append([prev_tx, prev_index, prev_amount, addr, locking_script, block])
                            with open(f'{r_user}_utxos.csv', 'w') as utxo_file:
                                writer = csv.writer(utxo_file)
                                writer.writerows(utxos)
                            print(f"{r_user} recieved {prev_amount} satoshis")
        except SyntaxError:
            print("recieved an invalid script")

def get_height():
    with open("block_log.csv", "r") as block_file:
        r = csv.reader(block_file)
        lines = list(r)
        return int(lines[-1][1])

def write_block(block_hash):
    with open("block_log.csv", "a", newline="") as block_file:
        writer = csv.writer(block_file)
        height = get_height() + 1
        writer.writerow((block_hash, height))
    print(f"Recieved Block: {block_hash} at height: {height}")

def utxo_reset(block_hash):
    users = get_all_users()
    for user in users:
        with open(f"{user}_utxos.csv", 'r') as utxo_file:
            r = csv.reader(utxo_file)
            utxos = list(r)
            for i, utxo in enumerate(utxos):
                if utxo[5] == block_hash:
                    utxos.pop(i)
        with open(f"{user}_utxos.csv", "w") as utxo_file:
            w = csv.writer(utxo_file)
            w.writerows(utxos)

def remove_blocks():
    with open("block_log.csv", "r") as block_file:
        r = csv.reader(block_file)
        blocks = list(r)
    for i in range(10):
        block_hash = blocks.pop()[0]
        utxo_reset(block_hash)
    with open("block_log.csv", "w", newline="") as block_file:
        w = csv.writer(block_file)
        w.writerows(blocks)

def all_hashes():
    with open("block_log.csv", "r") as block_file:
        r = csv.reader(block_file)
        lines = list(r)
        blocks = []
        for line in lines:
            blocks.append(line[0])
    return blocks

def sync_phase(node, then_hash):
    start_block = bytes.fromhex(then_hash)
    getheaders = GetHeadersMessage(start_block=start_block)
    node.send(getheaders)
    headers = node.wait_for(HeadersMessage)
    last_block = bytes.fromhex(then_hash)

    getdata = GetDataMessage()
    
    for block in headers.blocks:
        if not block.check_pow():
            raise RuntimeError('pow is invalid')
        if block.prev_block!= last_block:
            raise RuntimeError('chain broken')
        getdata.add_data(FILTERED_BLOCK_DATA_TYPE, block.hash())
        all_blocks = all_hashes()
        if block.hash().hex() in all_blocks:
            pass
        else:
            write_block(block.hash().hex())
        last_block = block.hash()
    node.send(getdata)

def block_syncer():
    node = SimpleNode(HOST, testnet=True, logging=False)
    node.handshake()
    while True:
        now_hash = get_latest_block_hash()
        then_hash = read_log(-1)
        current_addr = get_all_addr()
        bf = BloomFilter(size=30, function_count=5, tweak=1729)
        if now_hash != then_hash:
            for addr in current_addr:
                h160 = decode_base58(addr)
                bf.add(h160)
            node.send(bf.filterload())
            invalid = True
            while invalid:
                try:
                    sync_phase(node, then_hash)
                    invalid = False
                except RuntimeError as e:
                    print(e)
                    remove_blocks()
                    then_hash = read_log(-1)
            signal.signal(signal.SIGALRM, handler)
            signal.alarm(40)
            try:
                input_parser(current_addr, node)
            except Exception as e:
                print(e)
        time.sleep(10)

