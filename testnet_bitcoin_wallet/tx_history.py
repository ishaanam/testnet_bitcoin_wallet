import csv

from block_utils import get_known_height, get_height

def get_tx_history(username, show_unconfirmed=False):
    tx_history = []
    latest_height = int(get_known_height())
    with open(f"{username}_utxos.csv", 'r') as utxo_file:
        r = csv.reader(utxo_file)
        txs = list(r)
    for tx in txs:
        # transaction hash, amount, confirmation status, #of confirmations
        block_hash = tx[-2]
        confirmations = latest_height - get_height("block_log.csv", block_hash)
        if tx[-1] == '0': 
            status = "belongs to an unconfirmed transaction" 
        elif tx[-1] == '1':
            status = "unspent"
        elif tx[-1] == '2' or tx[-1] == '3':
            status = "spent"
        
        if status == "unconfirmed transaction":
            if show_unconfirmed:
                tx_history.append(tx[0], tx[2], status, 0) 
        else:   
            tx_history.append([tx[0], tx[2], status, confirmations]) 
    return tx_history
            
def format_tx_history(username):
    option = input("Would you like to see unconfirmed unspent transaction outputs as well[y/n]: ")
    if option == "y":
        show_unconfirmed = True
    else:
        show_unconfirmed = False
    tx_history = get_tx_history(username, show_unconfirmed)
    for tx in tx_history:
        print("\n")
        print("TRANSACTION")
        print(f"Transaction ID: {tx[0]}")
        print(f"Amount (Satoshis): {tx[1]}")
        print(f"Confirmation Status: {tx[2]}")
        print(f"# of Confirmations: {tx[3]}")

    print("\n")
