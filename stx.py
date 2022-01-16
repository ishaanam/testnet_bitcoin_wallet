#imports
import time

from ProgrammingBitcoin.ecc import PrivateKey
from ProgrammingBitcoin.helper import hash256, little_endian_to_int, encode_varint, read_varint, decode_base58, SIGHASH_ALL
from ProgrammingBitcoin.script import p2pkh_script, Script
from ProgrammingBitcoin.tx import Tx, TxIn, TxOut
from ProgrammingBitcoin.network import SimpleNode
from network_settings import HOST
import csv
from jbok import make_address, get_pkobj

def get_balance(username):
	amount = 0
	with open(f'{username}_utxos.csv', 'r') as user_file:
		r = csv.reader(user_file)
		lines = list(r)
		for line in lines:
			amount += int(line[2])
	return amount

def sign_input(tx_obj, index, private_key):
	z = tx_obj.sig_hash(index)
	der = private_key.sign(z).der()
	sig = der + SIGHASH_ALL.to_bytes(1, 'big')
	sec = private_key.point.sec()
	script_sig = Script([sig, sec])
	tx_obj.tx_ins[index].script_sig = script_sig
	return tx_obj

def send_transaction(username):
	target_address = input("Recipient: ")
	try:
		target_h160 = decode_base58(target_address)
	except ValueError:
		print("invalid address")
		return None
	target_script = p2pkh_script(target_h160)
	try:
		target_amount = int(input("Amount: "))
		fee = int(input("Fee: "))
		if (target_amount + fee) > get_balance(username):
			print("Insufficient funds")
			return False
	except ValueError:
		print("invalid data type")
		return None

	with open(f"{username}.csv", "r") as key_file:
			r = csv.reader(key_file)
			keys = list(r)

	with open(f"{username}_utxos.csv", 'r') as user_file:
		r = csv.reader(user_file)
		utxos = list(r)

	my_tx_ins = []
	my_wallets = []
	used_utxos = []

	used_amount = 0
	for utxo in utxos:
		print(utxos)
		used_amount += int(utxo[2])
		prev_tx = bytes.fromhex(utxo[0])
		used_utxos.append(prev_tx)
		prev_index = int(utxo[1])
		my_tx_ins.append(TxIn(prev_tx, prev_index))
		for key in keys:
			if key[1] == utxo[3]:
				my_wallets.append(key[0])
		if used_amount >= (target_amount + fee):
			break

	my_tx_outs = []
	if used_amount > (target_amount + fee):
		change_address = make_address(username)
		change_h160 = decode_base58(change_address)
		change_script = p2pkh_script(change_h160)
		my_tx_outs.append(TxOut(amount=(used_amount - target_amount - fee), script_pubkey=change_script))

	my_tx_outs.append(TxOut(amount=target_amount, script_pubkey=target_script))

	tx_obj = Tx(1, my_tx_ins, my_tx_outs, 0, True)

	for i, tx_in in enumerate(tx_obj.tx_ins):
		private_key = get_pkobj(my_wallets[i])
		z = tx_obj.sig_hash(i)
		der = private_key.sign(z).der()
		sig = der + SIGHASH_ALL.to_bytes(1, 'big')
		sec = private_key.point.sec()
		script_sig = Script([sig, sec])
		tx_obj.tx_ins[i].script_sig = script_sig

	print(tx_obj.serialize().hex())
	print("\n")
	for tx_in in tx_obj.tx_ins:
		print(tx_in)
	print("tx outs")
	for tx_out in tx_obj.tx_outs:
		print(tx_out)

	node = SimpleNode(HOST, testnet=True, logging=False)
	node.handshake()
	node.send(tx_obj)
	print('tx sent!')

	#deleting utxos from utxo pool
	del_length = len(tx_obj.tx_ins) #3
	real_len = 0

	while del_length > real_len:
		utxos.pop(real_len)
		real_len += 1

	with open(f'{username}_utxos.csv', 'w') as new_file:
		writer = csv.writer(new_file)
		writer.writerows(utxos)
