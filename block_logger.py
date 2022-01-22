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
            w.writerow((start_block, 0))
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


def input_parser(current_addr, node):
    while True:
        try:
            message = node.wait_for(MerkleBlock, Tx)
            if message.command == b'merkleblock':
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
                            with open(f'{r_user}_utxos.csv', 'a', newline="") as utxo_file:
                                tupl = (prev_tx, prev_index, prev_amount, addr, locking_script)
                                writer = csv.writer(utxo_file)
                                writer.writerow(tupl)
                            print(f"{r_user} recieved {prev_amount} satoshis")
        except SyntaxError:
            print("recieved an invalid script")



def block_syncer():
    while True:
        now_hash = get_latest_block_hash()
        then_hash = read_log(-1)
        current_addr = get_all_addr()
        node = SimpleNode(HOST, testnet=True, logging=False)
        bf = BloomFilter(size=30, function_count=5, tweak=1729)

        if now_hash != then_hash and then_hash != None:
            for addr in current_addr:
                h160 = decode_base58(addr)
                bf.add(h160)
            node.handshake()
            node.send(bf.filterload())

            start_block = bytes.fromhex(then_hash)

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
            last_block = last_block.hex()
            print(f"Recieved Block: {last_block}")
            with open('block_log.csv', 'a', newline="") as block_file:
                writer = csv.writer(block_file)
                writer.writerow((last_block, 0))
            node.send(getdata)

            signal.signal(signal.SIGALRM, handler)
            signal.alarm(30)

            try:
                input_parser(current_addr, node)
            except Exception as e:
                print(e)
        time.sleep(10)




