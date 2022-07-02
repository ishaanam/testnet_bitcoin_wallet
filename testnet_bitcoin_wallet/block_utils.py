import csv
import logging
import signal
from os.path import exists
import socket
from enum import Enum

from ProgrammingBitcoin.block import Block
from ProgrammingBitcoin.helper import decode_base58
from ProgrammingBitcoin.network import (
    GetDataMessage,
    GetHeadersMessage,
    HeadersMessage,
    SimpleNode,
    FILTERED_BLOCK_DATA_TYPE,
)
from ProgrammingBitcoin.tx import Tx
from ProgrammingBitcoin.bloomfilter import BloomFilter
from ProgrammingBitcoin.merkleblock import MerkleBlock

class TXOState(Enum):
    UNCONFIRMED_UTXO = "0"
    CONFIRMED_UTXO = "1"
    UNCONFIRMED_STXO = "2"
    CONFIRMED_STXO = "3"

class InvalidNodeError(Exception):
    pass

class UTXONotFoundError(Exception):
    pass

def set_node(new_host):
    with open("network_settings.py", "w") as net_file:
        net_file.write(f"HOST = '{new_host}'")

def get_node():
    try:
        from network_settings import HOST
        return HOST
    except (ModuleNotFoundError, ImportError):
        HOST = "testnet.programmingbitcoin.com"
        set_node(HOST)
        return HOST

HOST = get_node()

logging.basicConfig(filename='block.log', format='%(levelname)s:%(message)s', level=logging.DEBUG)

# If block_log.csv file doesn't exist, this function will create one
def start_log():
    start_block = "000000000000012ad603ddcc526791f6b2046a887999a284d60c44599536fced"
    start_height =  2164464
    next_block = "0000000000006421447d155fc4007170cab0d98a06448dbaf74435be86082a8e"
    next_height =2164465
    with open("block_log.csv", "w", newline="") as block_log:
        w = csv.writer(block_log)
        w.writerows([(start_block, start_height), (next_block, next_height)])

# ensures that a new node is valid before updating network_settings.py
def is_valid_node(host):
    try:
        node = SimpleNode(host, testnet=True, logging=False)
        return True
    except (socket.gaierror, TimeoutError, ConnectionRefusedError):
        raise InvalidNodeError("That appears to be an invalid node please try another node or keep using the previous node.")

# reads from block_log.csv and returns the specified block hash
def read_log(block_number):
    with open('block_log.csv', 'r') as log_file:
        r = csv.reader(log_file)
        lines = list(r)
        return lines[block_number][0]

# get the latest block hash which the node we've connected to knows about
def get_latest_block_hash():
    node = SimpleNode(HOST, testnet=True, logging=False)
    node.handshake()
    start_block = bytes.fromhex(read_log(-1))

    getheaders = GetHeadersMessage(start_block=start_block)
    node.send(getheaders)

    headers = node.wait_for(HeadersMessage)

    try:
        return headers.blocks[-1].hash().hex()
    except IndexError:
        return get_known_hash()

def get_known_height():
    with open("block_log.csv", "r") as block_log:
        r = csv.reader(block_log)
        blocks = list(r)
    return int(blocks[-1][1])

def get_known_hash():
    with open('block_log.csv', 'r') as block_log:
        r = csv.reader(block_log)
        blocks = list(r)
    return blocks[-1][0]

# checks if latest block hash from node is the same as the most recent one in block_log.csv
def is_synched():
    now_hash = get_latest_block_hash()
    then_hash = read_log(-1)
    if now_hash == then_hash:
        return True
    return False

# get the height of a block given the file and a block hash
def get_height(block_hash):
    with open("block_log.csv", "r") as block_file:
        r = csv.reader(block_file)
        blocks = list(r)
    for block in blocks:
        if block[0] == block_hash:
            return int(block[1])
    return 0

# find which user an address belongs to
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

# returns a list of all users
def get_all_users():
    users = []
    try:
        with open('users.csv', 'r') as user_file:
            r = csv.reader(user_file)
            lines = list(r)
            for line in lines:
                users.append(line[0])
    except FileNotFoundError:
        pass
    return users

# returns a list of all addresses
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
    raise RuntimeError("timed out")

# get block hash hex given a MerkleBlock object
def get_block_hex(m):
    block = Block(m.version, m.prev_block, m.merkle_root, m.timestamp, m.bits, m.nonce)
    return block.hash().hex()

def write_block(prev_block, block_hash, num_blocks):
    height = get_known_height() + num_blocks
    with open("block_log.csv", "a", newline="") as block_file:
        w = csv.writer(block_file)
        w.writerow((block_hash, height))
    return None

# gets all transaction ids
def get_all_ids():
    users = get_all_users()
    ids = []
    for user in users:
        with open(f"{user}_utxos.csv", "r") as utxo_file:
            r = csv.reader(utxo_file)
            utxos = list(r)
            for utxo in utxos:
                ids.append([utxo[0], utxo[1], user])
    return ids

# set tx flag to 0
def tx_set_new(user, tx_id, index, amount, address, scriptPubKey, block_hash, height):
    with open(f"{user}_utxos.csv", 'a', newline="") as utxo_file:
        w = csv.writer(utxo_file)
        w.writerow([tx_id, index, amount, address, scriptPubKey, block_hash, TXOState.UNCONFIRMED_UTXO.value, height])

# set tx flag to 1
def tx_set_confirmed(user, tx_id, index=None, amount=None, address=None, scriptPubKey=None, block_hash=None, height=None):
    with open(f"{user}_utxos.csv", 'r') as utxo_file:
        r = csv.reader(utxo_file)
        utxos = list(r)
        existing_index= None
        for i, utxo in enumerate(utxos):
            if utxo[0] == tx_id:
                existing_index = i
    if existing_index != None:
        utxos[existing_index][6] = TXOState.CONFIRMED_UTXO.value
        utxos[existing_index][5] = block_hash
        utxos[existing_index][7] = height
    elif existing_index == None and address:
        utxos.append([tx_id, index, amount, address, scriptPubKey, block_hash, TXOState.CONFIRMED_UTXO.value, height])
    else:
        raise UTXONotFoundError("Unable to find unconfirmed utxo to set as confirmed")
    with open(f"{user}_utxos.csv", 'w', newline="") as utxo_file:
        w = csv.writer(utxo_file)
        w.writerows(utxos)

# set other flags(2, 3, sometimes 0)
def tx_set_flag(user, tx_id, flag, index=None, block_height=None, block_hash=None):
    existing_index = None
    with open(f"{user}_utxos.csv", 'r') as utxo_file:
        r = csv.reader(utxo_file)
        utxos = list(r)
        for i, utxo in enumerate(utxos):
            if utxo[0] == tx_id and index != None and utxo[1] == index:
                existing_index = i
            elif utxo[0] == tx_id and index == None:
                existing_index = i
    if existing_index == None:
        raise UTXONotFoundError("Unable to find transction to set flag")

    if flag:
        utxos[existing_index][6] = int(flag)
    if block_height:
        utxos[existing_index][7] = block_height
    if block_hash:
        utxos[existing_index][5] = block_hash

    with open(f"{user}_utxos.csv", 'w') as utxo_file:
        w = csv.writer(utxo_file)
        w.writerows(utxos)

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
                ids = get_all_ids()
                for i, tx_out in enumerate(message.tx_outs):
                    for addr in current_addr:
                        if tx_out.script_pubkey.address(testnet=True) == addr:
                            prev_tx = message.hash().hex()
                            r_user = find_user(addr)
                            if prev_tx in old_utxos:
                                tx_set_flag(r_user,prev_tx, TXOState.CONFIRMED_UTXO.value)
                                old_utxos.remove(prev_tx)
                            else:
                                prev_index = i
                                prev_amount = tx_out.amount
                                locking_script = tx_out.script_pubkey
                                block = get_block_hex(merkle_block)
                                tx_set_confirmed(r_user, prev_tx, index, prev_amount, addr, locking_script, block)
                    for i, tx_in in enumerate(message.tx_ins):
                        for tx_id in ids:
                            if tx_id[0] == tx_in.prev_tx.hex() and int(tx_id[1]) == tx_in.prev_index:
                                tx_set_flag(tx_id[2], tx_id[0], TXOState.CONFIRMED_STXO.value, tx_id[1])
        except SyntaxError:
            logging.info("received an invalid script")

# reorg given the fork file
def reorg(fork):
    node = SimpleNode(HOST, testnet=True, logging=False)
    with open(fork, "r") as fork_file:
        r = csv.reader(fork_file)
        fork_file= list(r)
        forking_point = fork_file[0]
    
    with open("block_log.csv", "r") as main_file:
        r = csv.reader(main_file)
        main_file = list(r)
    
    new_blocks = fork_file[1:]
    fork_file = [fork_file[0]]
    fork_len = len(new_blocks)
    main_len = len(main_file) - main_file.index(forking_point) - 1
    old_blocks = main_file[-main_len:]
    main_file= main_file[:-main_len]
    main_file = main_file + new_blocks 
    fork_file = fork_file + old_blocks

    # replace blocks in block file and fork file
    with open(fork, "w", newline="") as file:
        w = csv.writer(file)
        w.writerows(fork_file)
    with open("block_log.csv", "w", newline="") as file:
        w = csv.writer(file)
        w.writerows(main_file)
    old = [block[0] for block in old_blocks]
    # unconfirm utxos mined in blocks that were reorged out
    for user in get_all_users():
        old_utxos = []
        with open(f"{user}_utxos.csv", 'r') as utxo_file:
            r = csv.reader(utxo_file)
            utxos = list(r)
            for utxo in utxos:
                if utxo[5] in old:
                    old_utxos.append(utxo[0])
                    tx_set_flag(user, utxo[0], TXOState.UNCONFIRMED_UTXO.value)
    # get utxos mined in the new blocks and figure out if any users have been double-spent 
    current_addr = get_all_addr()
    bf = BloomFilter(size=30, function_count=5, tweak=1729)
    for addr in current_addr:
        bf.add(decode_base58(addr))
    node.send(bf.filterload())
    getdata = GetDataMessage()

    for block in new_blocks:
        getdata.add_data(FILTERED_BLOCK_DATA_TYPE, bytes.fromhex(block[0]))
    node.send(getdata)
    signal.signal(signal.SIGALRM, handler)
    signal.alarm(10)
    try:
        input_parser(current_addr, node)
    except RuntimeError:
        logging.info(f"a reorg of {main_len} blocks has occured")
        if old_utxos != []:
            logging.info(f"You may have been double spent with the following transactions: {old_utxos}")
