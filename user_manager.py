import csv
import getpass
from hashlib import sha256
from block_logger import get_all_users
from hd import new_tprv

def save_pass(password):
    password = sha256(password.encode())
    return password.hexdigest()

def make_user():
    no_user = True
    while no_user:
        username = input("username: ")
        try:
            current_users = get_all_users()
        except FileNotFoundError:
            current_users = []
        if username in current_users:
            print("This username is already taken")
        else:
            no_user = False
    no_pass = True
    while no_pass:
        password = getpass.getpass(prompt="password: ")
        confirm_password = getpass.getpass(prompt="confirm password: ")
        if password == confirm_password:
            print(f"Password confirmed, you are now logged in as {username}")
            no_pass = False
        else:
            print("The passwords don't match")
    pass_hash = save_pass(password)
    tprv = new_tprv()
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

    return username

def user_login():
    not_in = True
    while not_in:
        username = input("username: ")
        password = getpass.getpass(prompt="password: ")
        with open('users.csv', 'r') as user_file:
            csv_reader = csv.reader(user_file)
            for line in csv_reader:
                if line[0] == username and line[1] == save_pass(password):
                    print(f"You are now successfully logged in {username}")
                    return (line[0])
                elif line[0] == username:
                    print("incorrect password")

def has_login():
    not_logged = True
    while not_logged:
        account = input("Do you already have an account?[y/n]:")
        if account == "y":
            starter_info = user_login()
            not_logged = False
            return starter_info
        elif account == "n":
            starter_info = make_user()
            not_logged = False
            return starter_info
        else:
            print("I don't understand ")



