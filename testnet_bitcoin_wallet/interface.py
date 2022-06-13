from socket import gaierror
from enum import Enum

from jbok import get_tpub, get_tprv, make_address
from network_interface import is_online
from block_logger import initial_connect
from block_utils import is_synched, is_valid_node, set_node
from stx import get_balance, construct_transaction, broadcast_transaction, TransactionConstructionError, get_balance
from tx_history import get_tx_history

class Colors(Enum):
    PURPLE = '\033[94m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    END = '\033[0m'

def balance(out_func, pipe, lock, username):
    # If wallet is not fully synchronized, let them know but still show them their balance so far
    if not is_online(pipe, lock):
        out_func("Please note that your wallet is currently offline so your balance has not been updating.")
    elif is_synched() == False:
        out_func("Please note that your wallet is still in the process of synching with the blockchain.")
    balance = get_balance(username, unconfirmed=True)
    out_func(f"Your current balance is: {balance[0]} Satoshis")
    if balance[1] != 0:
        out_func(f"You also have an additional unconfirmed balance of {balance[1]} Satoshis")

def recieve(out_func, username):
    out_func(f"Here is your testnet address: {make_address(username)}")

def tpub(out_func, username):
    out_func(get_tpub(username))

def tprv(out_func, username):
    out_func(get_tprv(username))

def change_node(out_func, in_func):
    out_func("Note: confirmation may take ~1 minute")
    new_host = in_func(["New node"])[0]
    if is_valid_node(new_host):
        set_node(new_host)
        out_func("Please restart your wallet for these changes to take full affect everywhere")

def status(out_func, pipe, lock):
    # this feature also only works when the wallet is completely synchronized
    if is_online(pipe, lock):
        if is_synched():
            out_func("The wallet is fully synchronized with the blockchain")
        else:
            out_func("The wallet is in the process of synchronizing with the blockchain.")
        out_func(f"The latest known block height is: {get_known_height()}")
    else:
        out_func("You are currently running this wallet offline, so it is not connected to a full node")

def reconnect(out_func, pipe, lock, p_input, p):
    if is_online(pipe, lock):
        out_func("Your wallet is already online, there is no need to reconnect")
    else:
        try:
            initial_connect()
            p_input.send([True, "", True])
            p.start()
            out_func("Successfully connected to full node")
        except (gaierror, ConnectionRefusedError):
            out_func("Wallet still failed to connect")

def tx_history(out_func, in_func, pipe, lock, username):
    online = is_online(pipe, lock)
    if not online:
        out_func("Please note that your wallet is not synching with the blockchain right now because you are running this wallet offline")
    elif is_synched() == False:
        out_func("Please note that your wallet is still in the process of synching with the blockchain.")
    option = in_func(["Would you like to see unconfirmed unspent transaction outputs as well[y/n]"])[0]

    if option == "y":
        show_unconfirmed = True
    else:
        show_unconfirmed = False

    tx_history = get_tx_history(username, online, show_unconfirmed)
    for tx in tx_history:
        out_func("\n")
        out_func("TRANSACTION")
        out_func(f"Transaction ID: {tx[0]}")
        out_func(f"Amount (Satoshis): {tx[1]}")
        if tx[2] == "unconfirmed":
            out_func(f"Confirmation Status: {Colors.YELLOW.value}{tx[2]}{Colors.END.value}")
        elif tx[2] == "unspent":
            out_func(f"Confirmation Status: {Colors.PURPLE.value}{tx[2]}{Colors.END.value}")
        elif tx[2] == "spent":
            out_func(f"Confirmation Status: {Colors.RED.value}{tx[2]}{Colors.END.value}")
        out_func(f"# of Confirmations: {tx[3]}")

def send(out_func, in_func, pipe, lock, username):
    # do not allow user to send transactions until the wallet is fullly synchronized
    online = is_online(pipe, lock)
    if not online:
        out_func("Note: your wallet is currently running offline, so your transaction won't be broadcasted by this wallet")
    if not online or is_synched():

        num_r = int(in_func(["Number of recipients"])[0])

        recipients = []
        values = []

        for i in range(num_r):
            rv_pair = in_func([f"Recipient #{i+1}", "Amount"])
            recipients.append(rv_pair[0])
            values.append(int(rv_pair[1]))

        try:
            tx_obj, needs_change, used_utxos = construct_transaction(recipients, values, username)
            out_func("Hex Serialization")
            out_func(tx_obj.serialize().hex())
            out_func("Transaction ID")
            out_func(tx_obj.id())

            self_broadcast = None
            while self_broadcast != 'n' and self_broadcast != 'y':
                self_broadcast = in_func(["Did you broadcast this transaction yourself?[y/n]"])[0]

            broadcast_transaction(tx_obj, online, self_broadcast, needs_change, username, used_utxos)
        except TransactionConstructionError as e:
            out_func(e)


    else:
        out_func("Your wallet is currently in the process of synching with the blockchain. Please try again later.")

def storage(out_func, in_func, pipe, lock, username):
    # do not allow user to send transactions until the wallet is fullly synchronized
    online = is_online(pipe, lock)
    if not online:
        out_func("Note: your wallet is currently running offline, so your transaction won't be broadcasted by this wallet")
    elif is_synched() or not online:

        rv_pair = in_func([f"Recipient #{i+1}", "Amount"])
        recipients = [in_func(["Recipient"])]
        values = [get_balance(username)-400]

        try:
            tx_obj, needs_change = construct_transaction(recipients, values, username)
        except TransactionConstructionError as e:
            out_func(e)

        out_func("Hex Serialization")
        out_func(tx_obj.serialize().hex())
        out_func("Transaction ID")
        out_func(tx_obj.id())
        self_broadcast = None

        while self_broadcast != 'n' and self_broadcast != 'y':
            self_broadcast = in_func(["Did you broadcast this transaction yourself?[y/n]"])[0]

        broadcast_transaction(tx_obj, online, self_broadcast, needs_change, username)

    else:
        out_func("Your wallet is currently in the process of synching with the blockchain. Please try again later.")

