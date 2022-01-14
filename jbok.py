from secrets import token_hex
import csv
from helper import little_endian_to_int, hash256
from ecc import PrivateKey

def get_pkobj(seed):
	seed = str.encode(seed)
	secret = little_endian_to_int(hash256(seed))
	private_key = PrivateKey(secret)
	return private_key

def get_addr(seed):
	private_key = get_pkobj(seed)
	p = private_key.point
	return(p.address(testnet=True))

def make_address(username):
	hex_token = token_hex(32)
	address = get_addr(hex_token)
	with open(f'{username}.csv', 'a', newline="") as new_file:
		writer = csv.writer(new_file)
		writer.writerow((hex_token, address))
	return address
