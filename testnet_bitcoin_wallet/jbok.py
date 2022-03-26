import csv
from ProgrammingBitcoin.ecc import PrivateKey

from hd import HD_Key
from segwit import make_p2wpkh_address

def get_pkobj(seed):
    private_key = PrivateKey(int(seed, 16))
    return private_key

def get_addr(seed, version):
    private_key = get_pkobj(seed)
    p = private_key.point
    if version == "-1":
        return p.address(testnet=True)
    if version == "0":
        h160 = p.hash160() 
        return make_p2wpkh_address(h160)

def make_address(username):
    with open('users.csv', 'r') as user_file:
        r = csv.reader(user_file)
        lines = list(r)
        for i, line in enumerate(lines):
            if line[0] == username:
                tprv = line[2]
                index = int(line[3]) + 1
                lines[i][3] = index 
    key = HD_Key.parse_priv(tprv)
    ck = key.CKDpriv(index)
    version = get_version(username)
    address = get_addr(ck.k, version)
    with open(f'{username}.csv', 'a', newline="") as a_file:
        writer = csv.writer(a_file)
        writer.writerow((ck.k, address))
    
    with open('users.csv', 'w') as user_file:
        writer = csv.writer(user_file)
        writer.writerows(lines)
    return address

def get_tprv(username):
    with open('users.csv', 'r') as user_file:
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

def get_version(username):
    with open("users.csv", "r") as user_file:
        r = csv.reader(user_file)
        lines = list(r)
        for line in lines:
            if line[0] == username:
                version = line[4]
    return version
