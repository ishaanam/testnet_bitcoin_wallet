import time

from ProgrammingBitcoin.ecc import PrivateKey
from ProgrammingBitcoin.helper import hash256, little_endian_to_int, encode_varint, read_varint, decode_base58, SIGHASH_ALL
from ProgrammingBitcoin.script import p2pkh_script, Script 
from ProgrammingBitcoin.tx import Tx, TxIn, TxOut
from ProgrammingBitcoin.network import SimpleNode
from ProgrammingBitcoin.op import OP_CODE_FUNCTIONS
import csv
from jbok import make_address, get_pkobj

try:
    from network_settings import HOST
except (ModuleNotFoundError, ImportError):
    with open("network_settings.py", "w") as net_file:
        net_file.write('HOST = "testnet.programmingbitcoin.com"')
        from network_settings import HOST

def get_balance(username):
    amount = 0
    with open(f'{username}_utxos.csv', 'r') as user_file:
        r = csv.reader(user_file)
        lines = list(r)
        for line in lines:
            amount += int(line[2])
    return amount

def make_p2pkh_script(s):
    p2pkh_script = [0x76, 0xa9, "", 0x88, 0xac]
    s = s.split()
    p2pkh_script[2] = bytes.fromhex(s[2])
    return Script(p2pkh_script)

def multi_send(username):
    num_r = input("Number of recipients: ")
    try:
        num_r = int(num_r)
        if num_r <= 0:
            print("Invalid number of recipients")
            return None
        fee = 300 + (100 * num_r)
    except ValueError:
        print("number of recipients must be an integer")
    my_tx_outs = []
    total_amount = fee
    try:
        for i in range(num_r):
            target_address = input(f"Recipient{i+1}: ")
            try:
                target_h160 = decode_base58(target_address)
            except ValueError:
                print("invalid address")
                return None
            target_script = p2pkh_script(target_h160)
            try:
                target_amount = int(input("Amount(in Satoshis): "))
            except ValueError:
                print("invalid amount")
                return None
            my_tx_outs.append(TxOut(amount=target_amount, script_pubkey=target_script))
            total_amount += target_amount
    except TypeError:
        print("Invalid number of recipients")
        return None
    
    if total_amount > get_balance(username):
        print("Insufficient funds")
        return None 

    my_tx_ins = []
    my_wallets = []
    my_script_sigs = []
    used_utxos = []
    used_amount = 0

    with open(f"{username}.csv", "r") as key_file:
        r = csv.reader(key_file)
        keys = list(r)

    with open(f"{username}_utxos.csv", 'r') as user_file:
        r = csv.reader(user_file)
        utxos = list(r)

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

    if used_amount > total_amount:
        change_address = make_address(username)
        change_h160 = decode_base58(change_address)
        change_script = p2pkh_script(change_h160)
        my_tx_outs.append(TxOut(amount=(used_amount - total_amount), script_pubkey=change_script))

    tx_obj = Tx(1, my_tx_ins, my_tx_outs, 0, True)

    for i, tx_in in enumerate(tx_obj.tx_ins):
        private_key = get_pkobj(my_wallets[i])
        script_pubkey = make_p2pkh_script(my_script_sigs[i])
        z = tx_obj.sig_hash(i, script_pubkey)
        der = private_key.sign(z).der()
        sig = der + SIGHASH_ALL.to_bytes(1, 'big')
        sec = private_key.point.sec()
        script_sig = Script([sig, sec])
        tx_obj.tx_ins[0].script_sig = script_sig
    
    print("hex serialization: ")
    print(tx_obj.serialize().hex())
    print("transaction id")
    print(tx_obj.id())

    node = SimpleNode(HOST, testnet=True, logging=False)
    node.handshake()
    node.send(tx_obj)
    print('tx sent!')

    del_length = len(tx_obj.tx_ins)
    real_len = 0

    while del_length > real_len:
        utxos.pop(0)
        real_len += 1
    with open(f'{username}_utxos.csv', 'w') as new_file:
        writer = csv.writer(new_file)
        writer.writerows(utxos)

