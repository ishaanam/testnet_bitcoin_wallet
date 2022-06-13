import socket
from os.path import exists
from multiprocessing import Process, Pipe

from ProgrammingBitcoin.network import SimpleNode
from block_logger import block_syncer, initial_connect
from block_utils import get_node

HOST = get_node()

def is_online(pipe, lock):
    p_input, p_output = pipe
    msg = p_output.recv()
    online = msg[0] 
    if not online and msg[2]:
        print(msg[1])
        print("Please ensure that your wallet and node are both online. In the mean time, your wallet is running in offline mode. This means that you cannot do things like broadcast transactions(though you can still create them) or download utxos. Once you restore connection, run 'reconnect'.")
    
    lock.acquire()
    try:
        p_input.send([online, msg[1], False])
    finally:
        lock.release() 
    
    return online

def run_network_interface(p_input, lock):
    try:
        node = SimpleNode(HOST, testnet=True, logging=False)
        # send list, [bool (online), string (error message), bool (new msg)]
        lock.acquire()
        try:
            p_input.send([True, "", True])
        finally:
            lock.release() 
        block_syncer(node)
    except (socket.gaierror, ConnectionRefusedError) as e:
        lock.acquire()
        try:
            p_input.send([False, e, True])
        finally:
            lock.release() 
