import socket

from ProgrammingBitcoin.network import SimpleNode
from block_logger import block_syncer
from block_utils import get_node

HOST = get_node()

def set_online(lock, msg):
    lock.acquire()
    msg[1] = msg[1][:-1]
    try:
        with open("online.txt", 'w') as online_file:
            online_file.write('\n'.join(msg))
    finally:
        lock.release()

def is_online(lock, out_func):
    with open("online.txt", 'r') as online_file:
        online = online_file.readline() == "True\n"
        error_msg = online_file.readline()
        msg_shown = online_file.readline() == "True"
    
    if not msg_shown:
        out_func(error_msg)
        out_func("Please ensure that your wallet and node are both online. In the mean time, your wallet is running in offline mode. This means that you cannot do things like broadcast transactions(though you can still create them) or download utxos. Once you restore connection, run 'reconnect'.")
        set_online(lock, [str(online), error_msg, "True"])

    return online

def run_network_interface(lock):
    try:
        node = SimpleNode(HOST, testnet=True, logging=False)
        set_online(lock, ["True", "", "True"])
        block_syncer(node)
    except (socket.gaierror, ConnectionRefusedError) as e:
        set_online(lock, ["False", str(e), "False"])
