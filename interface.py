from jbok import get_tpub, get_tprv
from user_manager import make_user, user_login, has_login
from stx import get_balance, multi_send
from rtx import recieve_tx
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
        print(f"Your current balance is: {get_balance(username)} Satoshis")
    elif option == "quit":
        active = False
    elif option == "sign out":
        username = has_login()
    elif option == "tpub":
        print(get_tpub(username))
    elif option == "tprv":
        print(get_tprv(username))
