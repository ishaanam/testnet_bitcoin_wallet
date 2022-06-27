import csv
from hashlib import sha256

from block_utils import get_all_users
from hd import HD_Key, InvalidSerializationError
from recover_funds import recover_funds, RecoverFundsError

class SignInError(Exception):
    pass

class UserCreationError(Exception):
    pass

def save_pass(password):
    password = sha256(password.encode())
    return password.hexdigest()

def sign_in(username, password):
    with open('users.csv', 'r') as user_file:
        csv_reader = csv.reader(user_file)
        for line in csv_reader:
            if line[0] == username and line[1] == save_pass(password):
                return True
            elif line[0] == username:
                raise SignInError("Incorrect password")
    raise SignInError("This username does not exist")

def create_user(username, password, out_func, password_in_func, words=None, tprv=None):
    try:
        current_users = get_all_users()
        if username in current_users:
            raise UserCreationError("This username is already taken")
    except FileNotFoundError:
        pass
    pass_hash = save_pass(password)
    if words:
        if len(words.split()) != 12:
            raise RecoverFundsError("Invalid words")
        tprv = HD_Key.recover_wallet(words)
    if tprv:
        HD_Key.parse_priv(tprv)

    if not words and not tprv:
        tprv = HD_Key.new_tprv(out_func, password_in_func)
    tupl = (username, pass_hash, tprv, 0)

    try:
        with open("users.csv", "a", newline="") as user_file:
            writer = csv.writer(user_file)
            writer.writerow(tupl)
    except FileNotFoundError:
        with open("users.csv", "w", newline="") as user_file:
            writer = csv.writer(user_file)
            writer.writerow(tupl)

    with open(f'{username}.csv', 'w', newline="") as new_file:
        writer = csv.writer(new_file)

    with open(f'{username}_utxos.csv', 'w', newline="") as utxo_file:
        writer = csv.writer(utxo_file)

    if tprv or words:
        # recover_funds
        pass

    return True
