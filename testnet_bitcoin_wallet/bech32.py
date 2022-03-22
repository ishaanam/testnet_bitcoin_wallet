def decode_bech32(address):
    confirmation = input("This doesn't appear to be a p2pkh address, would you like to make a segwit transaction output using this public key hash[y/n]: ")
    if confirmation == "y":
        return bytes.fromhex(address)
    else:
        raise ValueError("invalid address")
