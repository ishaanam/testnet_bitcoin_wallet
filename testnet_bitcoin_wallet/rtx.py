from jbok import make_address
from block_utils import gap_exceeded

def recieve_tx(username):
    passed = gap_exceeded(username)
    if not passed[0]: 
        print(f"Here is your testnet address: {make_address(username)}")
    else:
        proceed = input("You have exceeded the address creation gap limit because you have generated many addresses which haven't been used to send funds to. Would you still like to proceed?[y/n]: ")
        if proceed == "y":
            print(f"Here is your testnet address: {make_address(username)}")
        else:
            print(f"Here is an older address which funds haven't been sent to yet: {passed[1]}")
