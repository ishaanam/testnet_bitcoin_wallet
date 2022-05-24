import signal
import socket
from multiprocessing import Process, Pipe, Lock

from jbok import get_tpub, get_tprv
from user_manager import has_login
from send_to_storage import send_to_storage, get_all_balance
from stx import get_balance, multi_send
from rtx import recieve_tx
from block_utils import is_synched, get_known_height, handler, is_valid_node, start_log
from block_logger import initial_connect
from tx_history import format_tx_history
from network_interface import *

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
            # do not allow user to send transactions until the wallet is fullly synchronized
            if not is_online(pipe, lock):
                print("Note: your wallet is currently running offline, so your transaction won't be broadcasted by this wallet")
                multi_send(username, is_online(pipe, lock))
            elif is_synched():
                multi_send(username)
            else:
                print("Your wallet is currently in the process of synching with the blockchain. Please try again later.")

        # generate address for user to recieve funds
        elif option == "recieve":
            recieve_tx(username)

        # See balance (both confirmed and unconfirmed)
        elif option == "balance":
            # If wallet is not fully synchronized, let them know but still show them their balance so far
            if not is_online(pipe, lock):
                print("Please note that your wallet is currently offline so your balance has not been updating.")
            elif is_synched() == False:
                print("Please note that your wallet is still in the process of synching with the blockchain.")
            balance = get_balance(username, unconfirmed=True)
            print(f"Your current balance is: {balance[0]} Satoshis")
            if balance[1] != 0:
                print(f"You also have an additional unconfirmed balance of {balance[1]} Satoshis")

        elif option == "tpub":
            print(get_tpub(username))

        elif option == "tprv":
            print(get_tprv(username))

        elif option == "change node":
            print("Note: confirmation may take ~1 minute")
            new_host = input("New node: ")
            if is_valid_node(new_host):
                with open("network_settings.py", 'w') as net_file:
                    net_file.write(f'HOST = "{new_host}"')
                print("Please restart your wallet for these changes to take full affect everywhere")

        # allow user to send all funds in all accounts to a single address
        elif option == "storage":
            if get_all_balance() == 0:
                print("You have 0 testnet bitcoin")
            else:
                if not is_online(pipe, lock):
                    print("Note: your wallet is currently running offline, so your transaction won't be broadcasted by this wallet")
                    send_to_storage(is_online(pipe, lock))
                elif is_synched():
                    send_to_storage()
                else:
                    print("Your wallet is currently in the process of synching with the blockchain. Please try again later.")
        # checks how far the wallet it synchronized
        elif option == "status":
            # this feature also only works when the wallet is completely synchronized
            if is_online(pipe, lock):
                if is_synched():
                    print("The wallet is fully synchronized with the blockchain")
                else:
                    print("The wallet is in the process of synchronizing with the blockchain.")
                print(f"The latest known block height is: {get_known_height()}")
            else:
                print("You are currently running this wallet offline, so it is not connected to a full node")

        # show the user their full transaction history
        elif option == "tx history":
            if not is_online(pipe, lock):
                print("Please note that your wallet is not synching with the blockchain right now because you are running this wallet offline")
            elif is_synched() == False:
                print("Please note that your wallet is still in the process of synching with the blockchain.")
            format_tx_history(username, is_online(pipe, lock))

        elif option == "reconnect":
            if is_online(pipe, lock):
                print("Your wallet is already online, there is no need to reconnect")
            else:
                try:
                    initial_connect()
                    p_input.send([True, "", True])
                    p.start()
                    print("Successfully connected to full node")
                except (socket.gaierror, ConnectionRefusedError):
                    print("Wallet still failed to connect")


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
