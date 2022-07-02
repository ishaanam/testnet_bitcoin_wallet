import csv

from block_utils import get_known_height, get_height, is_synched

def get_tx_history(username, online, show_unconfirmed=False):
    if online:
        synched = is_synched()
    tx_history = []
    latest_height = get_known_height()
    with open(f"{username}_utxos.csv", 'r') as utxo_file:
        r = csv.reader(utxo_file)
        txs = list(r)
    for tx in txs:
        # transaction hash, amount, confirmation status, #of confirmations
        block_hash = tx[-2]
        if online:
            if synched:
                confirmations = latest_height - get_height(block_hash) + 1
            else:
                confirmations = "unknown (synchronizing)"
        else:
            confirmations = "unknown (offline)"
        if tx[6] == '0':
            status = "unconfirmed" 
        elif tx[6] == '1':
            status = "unspent"
        elif tx[6] == '2' or tx[6] == '3':
            status = "spent"
        
        if status == "unconfirmed transaction":
            if show_unconfirmed:
                tx_history.append(tx[0], tx[2], status, 0) 
        else:   
            tx_history.append([tx[0], tx[2], status, confirmations]) 
    return tx_history
