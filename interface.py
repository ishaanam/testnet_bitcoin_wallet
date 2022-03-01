from multiprocessing import Process

from jbok import get_tpub, get_tprv
from user_manager import make_user, user_login, has_login
from sent_to_storage import send_to_storage, get_all_balance
from stx import get_balance, multi_send
from rtx import recieve_tx
from block_logger import block_syncer

def run_wallet():
    print("NOTE: this wallet only operates on the testnet, enter 'sign out' to log into a different account and 'quit' to exit.")

    username = has_login()
    print("I can: calculate your current balance[cb], send transactions[stx], recieve transactions[rtx], and get your extended public key [tpub] or your extended private key[tprv]")

    active = True
    while active:
        print("What can I help you with?")
        option = input("You: ")
        if option == "stx":
            multi_send(username)
        elif option == "rtx":
            recieve_tx(username)
        elif option == "cb":
            balance = get_balance(username, unconfirmed=True)
            print(f"Your current balance is: {balance[0]} Satoshis")
            if balance[1] != 0:
                print(f"You also have an additional unconfirmed balance of {balance[1]} Satoshis")
        elif option == "quit":
            active = False
        elif option == "sign out":
            username = has_login()
        elif option == "tpub":
            print(get_tpub(username))
        elif option == "tprv":
            print(get_tprv(username))
        elif option == "storage":
            if get_all_balance() == 0:
                print("You have 0 testnet bitcoin")
            else:
                send_to_storage() 

if __name__ == '__main__':
    
    p = Process(target=block_syncer)
    p.start()
    run_wallet()
    p.terminate()
