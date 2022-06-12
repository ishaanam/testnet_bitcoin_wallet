import signal
import socket
from multiprocessing import Process, Pipe, Lock

from user_manager import has_login
from block_utils import is_synched, get_known_height, handler, is_valid_node, start_log
from block_logger import initial_connect
from network_interface import *
from interface import *

def cli_input(requests):
    results = []
    for request in requests:
        cl_in = input(f"{request}: ")
        results.append(cl_in)
    return results

def run_wallet(p, pipe, lock):
    print("NOTE: this wallet only operates on the testnet, enter 'sign out' to log into a different account and 'quit' to exit.")

    # ask user to login and obtain their username
    username = has_login()
    print("I can: calculate your current balance[balance], send transactions[send], recieve transactions[recieve], check if your wallet is fully synchronized with the blockchain[status], send all of your testnet bitcoin in all accounts to a specified address[storage], change the full node you get information from[change node], display your full transaction history[tx history] and get your extended public key [tpub] or your extended private key[tprv]")

    p_input, p_output = pipe
    try:
        initial_connect()
        p.start()
    except ConnectionRefusedError as e:
        p_input.send([False, e, True])
    # initial_connect()

    active = True
    # until user enters "quit"
    while active:
        option = input(">>> ")

        # send transaction
        if option == "send":
            send(print, cli_input, pipe, lock, username)

        # generate address for user to recieve funds
        elif option == "recieve":
            recieve(print, username)

        # See balance (both confirmed and unconfirmed)
        elif option == "balance":
            balance(print, pipe, lock, username)

        elif option == "tpub":
            tpub(print, username)

        elif option == "tprv":
            tprv(print, username)

        elif option == "change node":
            change_node(print, cli_input)

        # allow user to send all funds in all accounts to a single address
        elif option == "storage":
            storage(print, cli_input, pipe, lock, username)

        # checks how far the wallet it synchronized
        elif option == "status":
            status(print, pipe, lock)

        # show the user their full transaction history
        elif option == "tx history":
            tx_history(print, cli_input, pipe, lock, username)

        elif option == "reconnect":
            reconnect(print, pipe, lock, cli_input, p)

        # allow user to sign into a different account
        elif option == "sign out":
            username = has_login()

        elif option == "quit":
             active = False
             try:
                 p.terminate()
             except AttributeError:
                pass

if __name__ == '__main__':
    lock = Lock()
    p_input, p_output = Pipe()
    p = Process(target=run_network_interface, args=(p_input,lock))
    try:
        run_wallet(p, (p_input, p_output), lock)
    except KeyboardInterrupt:
        try:
            p.terminate()
        except AttributeError:
            pass
