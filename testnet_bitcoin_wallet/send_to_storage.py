from ProgrammingBitcoin.helper import decode_base58, SIGHASH_ALL
from ProgrammingBitcoin.script import p2pkh_script, Script 
from ProgrammingBitcoin.tx import Tx, TxIn, TxOut
from ProgrammingBitcoin.network import SimpleNode
from stx import get_balance, get_all_utxos, make_p2pkh_script
from block_utils import get_all_users
from jbok import get_pkobj
import csv

try:
    from network_settings import HOST
except (ModuleNotFoundError, ImportError):
    with open("network_settings.py", "w") as net_file:
        net_file.write('HOST = "testnet.programmingbitcoin.com"')
        from network_settings import HOST

def get_all_balance():
    all_users = get_all_users()
    balance = 0
    for user in all_users:
        balance += get_balance(user)
    return balance
        

def send_to_storage():
    print("Please provide exactly one address to send the funds to. If you don't care where the testnet Bitcoin goes, enter 'default'")
    target_address = input("Address: ")
    if target_address == "default":
        target_address = "mi9oPqzbuww3dRmLZa2rDAvP27S6312Jwt"
    else:
        try:
            target_script = p2pkh_script(decode_base58(target_address))
        except ValueError:
            print("Invalid address")
            return
    
    fee = 400
    target_amount = get_all_balance() - fee 
    tx_out = TxOut(amount=target_amount,script_pubkey=target_script)
    my_tx_ins = []
    my_wallets = []
    my_script_sigs = []
    utxos = []
    used_utxos = []
    keys = []
    used_amount = 0 
    users = get_all_users()
    

    for user in users: 
        with open(f"{user}.csv", "r") as key_file:
            r = csv.reader(key_file)
            keys += list(r)
        utxos += get_all_utxos(user)

    for utxo in utxos:
        used_amount += int(utxo[2])
        prev_tx = bytes.fromhex(utxo[0])
        used_utxos.append(prev_tx)
        prev_index = int(utxo[1])
        script_sig = utxo[4]
        my_tx_ins.append(TxIn(prev_tx, prev_index))
        my_script_sigs.append(script_sig)
        for key in keys:
            if key[1] == utxo[3]:
                my_wallets.append(key[0])

    tx_obj = Tx(1, my_tx_ins, [tx_out], 0, True)

    for i, tx_in in enumerate(tx_obj.tx_ins):
        private_key = get_pkobj(my_wallets[i])
        script_pubkey = make_p2pkh_script(my_script_sigs[i])
        z = tx_obj.sig_hash(i, script_pubkey)
        der = private_key.sign(z).der()
        sig = der + SIGHASH_ALL.to_bytes(1, 'big')
        sec = private_key.point.sec()
        script_sig= Script([sig, sec])
        tx_obj.tx_ins[i].script_sig = script_sig

    print("hex serialization: ")
    print(tx_obj.serialize().hex())
    print("transaction id")
    print(tx_obj.id())

    node = SimpleNode(HOST, testnet=True, logging=False)
    node.handshake()
    node.send(tx_obj)

    for user in users:
        with open(f"{user}_utxos.csv", 'w') as utxo_file:
            w = csv.writer(utxo_file)

