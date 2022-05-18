import signal
from os.path import exists
from multiprocessing import Process

from jbok import get_tpub, get_tprv
from user_manager import has_login
from send_to_storage import send_to_storage, get_all_balance
from stx import get_balance, multi_send
from rtx import recieve_tx
from block_logger import block_syncer, initial_connect
from block_utils import is_synched, get_known_height, handler, is_valid_node, start_log
from tx_history import format_tx_history

def run_wallet(p):
    print("NOTE: this wallet only operates on the testnet, enter 'sign out' to log into a different account and 'quit' to exit.")

    # If the block_log.csv file has never been created, meaning the wallet has never been run
    if not exists("block_log.csv"):
        print("Wallet will take a few seconds to start up ...")
        # create block_log.csv
        start_log()
        # run block_syncer() for ten seconds 
        signal.signal(signal.SIGALRM, handler)
        signal.alarm(10)
        try:
            initial_connect()
            block_syncer()
        except RuntimeError:
            pass
    online = None
    while online == None:
        is_offline = input("Do you want to run this wallet offline? This would mean that you cannot do things like broadcast transactions(though you can still create them) or download utxos.[y/n]")
        if is_offline == 'y':
            online = False
        elif is_offline == 'n':
            online = True

    # ask user to login and obtain their username
    username = has_login()
    print("I can: calculate your current balance[balance], send transactions[send], recieve transactions[recieve], check if your wallet is fully synchronized with the blockchain[status], send all of your testnet bitcoin in all accounts to a specified address[storage], change the full node you get information from[change node], display your full transaction history[tx history] and get your extended public key [tpub] or your extended private key[tprv]")
    if online:
        # Start child proccess to run block_syncer()
        initial_connect()
        p.start()

    active = True
    # until user enters "quit"
    while active:
        print("What can I help you with?")
        option = input(">>> ")
        
        # send transaction
        if option == "send":
            # do not allow user to send transactions until the wallet is fullly synchronized
            if not online:
                print("Note: your wallet is currently running in 'offline mode', so your transaction won't be broadcasted by this wallet")
                multi_send(username, online)
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
            if not online:
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
                if not online:
                    print("Note: your wallet is currently running in 'offline mode', so your transaction won't be broadcasted by this wallet")
                    send_to_storage(online)
                elif is_synched():
                    send_to_storage()
                else:
                    print("Your wallet is currently in the process of synching with the blockchain. Please try again later.")
        # checks how far the wallet it synchronized
        elif option == "status":
            # this feature also only works when the wallet is completely synchronized
            if online:
                if is_synched():
                    print("The wallet is fully synchronized with the blockchain")
                else:
                    print("The wallet is in the process of synchronizing with the blockchain.")
                print(f"The latest known block height is: {get_known_height()}")
            else:
                print("You are currently running this wallet in 'offline mode', so it is not connected to a full node")

        # show the user their full transaction history
        elif option == "tx history":
            if not online:
                print("Please note that your wallet is not synching with the blockchain right now because you are running this wallet in 'offline mode'")
            elif is_synched() == False:
                print("Please note that your wallet is still in the process of synching with the blockchain.")
            format_tx_history(username, online)
        
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
    p = Process(target=block_syncer)
    try:
        run_wallet(p)
    except KeyboardInterrupt:
        try:
            p.terminate()
        except AttributeError:
            pass
