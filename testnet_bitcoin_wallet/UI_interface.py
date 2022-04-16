import json, csv, sys, signal, os
from os.path import exists, join
from multiprocessing import Process

from jbok import get_tpub, get_tprv
from user_manager import has_login, save_pass
from send_to_storage import send_to_storage, get_all_balance
from stx import get_balance, multi_send
from rtx import recieve_tx
from block_logger import block_syncer
from block_utils import is_synched, get_known_height, handler, is_valid_node, start_log
from tx_history import format_tx_history

username = None

def start_wallet(p):
    if not exists(join(sys.path[0], 'block_log.csv')):
        # print('Wallet will take a few seconds to start up ...')
        start_log()
        signal.signal(signal.SIGALRM, handler)
        signal.alarm(10)
        try:
            block_syncer()
        except RuntimeError:
            pass
    p.start()

def login(username, password):
    try:
        with open('users.csv', 'r') as user_file:
            csv_reader = csv.reader(user_file)
            for line in csv_reader:
                if line[0] == username and line[1] == save_pass(password):
                    return (line[0])
                elif line[0] == username:
                    return False
    except:
        print(str(sys.exc_info()))

def logout(p):
    user = None
    p.terminate()

if __name__ == '__main__':
    try:
        resultRes = {}
        try:
            os.chdir(sys.path[0])
            lines = json.loads(input().split('\n')[0])
            for dataMsg in lines:
                if (dataMsg['command'] == 'login'):
                    argsArr = dataMsg['args']
                    username = login(*argsArr)
                    if (username):
                        p = Process(target=block_syncer)
                        start_wallet(p)
                        resultRes[dataMsg['command']] = username
                    else :
                        resultRes[dataMsg['command']] = 'incorrect username or password'
                else:
                    if is_synched():
                        cust_func = locals()[dataMsg['command']]
                        argsArr = dataMsg['args']
                        result = cust_func(*argsArr)
                        resultRes[dataMsg['command']] = result
                    else:
                        resultRes[dataMsg['command']] = 'Please note that your wallet is still in the process of synching with the blockchain.'
        except:
            resultRes[dataMsg['command']] = str(sys.exc_info())
        print(json.dumps(resultRes))
    except:
        resultRes['Error'] = 'Unable to execute script'
        print(json.dumps(resultRes))
