from secrets import token_hex
import csv
from ProgrammingBitcoin.helper import little_endian_to_int, hash256
from ProgrammingBitcoin.ecc import PrivateKey
from hd import HD_Key

def get_pkobj(seed):
	private_key = PrivateKey(int(seed, 16))
	return private_key

def get_addr(seed):
	private_key = get_pkobj(seed)
	p = private_key.point
	return(p.address(testnet=True))

def make_address(username):
    with open(f'users.csv', 'r') as user_file:
        r = csv.reader(user_file)
        lines = list(r)
        for i, line in enumerate(lines):
            if line[0] == username:
                tprv = line[2]
                index = int(line[3]) + 1
                lines[i][3] = index 
    key = HD_Key.parse_priv(tprv)
    ck = key.CKDpriv(index)
    address = get_addr(ck.k)
    with open(f'{username}.csv', 'a', newline="") as a_file:
        writer = csv.writer(a_file)
        writer.writerow((ck.k, address))
    
    with open(f'users.csv', 'w') as user_file:
        writer = csv.writer(user_file)
        writer.writerows(lines)
    return address

def get_tprv(username):
    with open(f'users.csv', 'r') as user_file:
        r = csv.reader(user_file)
        lines = list(r)
        for line in lines:
            if line[0] == username:
                tprv = line[2]
        return tprv

def get_tpub(username):
    tprv = get_tprv(username)
    key = HD_Key.parse_priv(tprv)
    tpub = key.serialize()
    return tpub
