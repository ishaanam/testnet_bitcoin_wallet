import os
import shutil
import csv
import unittest

from block_utils import TXOState, tx_set_confirmed
from stx import get_balance, construct_transaction, get_all_utxos, broadcast_transaction

TEST_USERNAME = "test_data/satoshi"

def add_user(username, key_hash, tprv, keys_created):
    with open("users.csv", 'a') as users_file:
        w = csv.writer(users_file)
        w.writerow((username, key_hash, tprv, keys_created))

def remove_user(username):
    with open("users.csv", 'r') as users_file:
        r = csv.reader(users_file)
        lines = list(r)
        for user in lines:
            if user[0] == username:
                lines.remove(user)

    with open("users.csv", 'w') as users_file:
        if lines:
            w = csv.writer(users_file)
            w.writerows(lines)

def add_key(username, key, address):
    with open(f"{username}.csv", 'a', newline="") as key_file:
        w = csv.writer(key_file)
        w.writerow((key, address))


def add_utxo(username, txid, index, amount, address, script, block_hash, txo_state):
    with open(f"{username}_utxos.csv", 'a', newline="") as user_file:
        w = csv.writer(user_file)
        w.writerow((txid, index, amount, address, script, block_hash, txo_state))


class TestWallet(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.mkdir("test_data")

        # temporarily add user to username.csv
        add_user(TEST_USERNAME, "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "tprv8ZgxMBicQKsPddYsUVeQPPe3JYTB2cFHhg631ErxiBUKhUsATYaH8HN31jkXzyq93hPFFEkpPrjASPgJAqfD8crik52mJbF51i7Xk5nophS", 2)

        # add keys and corresponding addresses
        key, address = "d49d8e25937141ddadfc58aa3ad1668ca0f5b2efd9413038ebc4c37de5a99f1d", "mpWbRKDEx5ovhTCptxPpvFJDmaeqjCk8Qi"
        add_key(TEST_USERNAME, key, address)

        key, address = "85ddc211e767c1e44144a64f6493582222fd69a9c3032a240d32903c6bb87b18", "mk6ii35iVXaHWbpeWuksPS4KrMryh8rXfD"
        add_key(TEST_USERNAME, key, address)

        # add two utxos to construct transactions with
        txid, index, amount, address, script, block_hash, txo_state = "dd547187c1b24b13ac1ecdb6a9b746cd41d2f75798c0b4527d4e5c418b8368dd", 1, 6000, "mpWbRKDEx5ovhTCptxPpvFJDmaeqjCk8Qi", "OP_DUP OP_HASH160 62a7b4e6243de334957e6dcfa4ea126c2e16dc8f OP_EQUALVERIFY OP_CHECKSIG", "0", TXOState.CONFIRMED_UTXO.value
        add_utxo(TEST_USERNAME, txid, index, amount, address, script, block_hash, txo_state)

        txid, index, amount, address, script, block_hash, txo_state = "5c029f8d65fdc42d6c014cc414691b6947429b2fbebeda849747fb097a7487bc", 1, 4000, "mk6ii35iVXaHWbpeWuksPS4KrMryh8rXfD", "OP_DUP OP_HASH160 32434deca73d57df98523d8348e7e6e5670dbc03 OP_EQUALVERIFY OP_CHECKSIG", "0", TXOState.CONFIRMED_UTXO.value
        add_utxo(TEST_USERNAME, txid, index, amount, address, script, block_hash, txo_state)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree("test_data")
        remove_user(TEST_USERNAME)

    def test_balance(self):
        target_balance = 10000
        user_balance = get_balance(TEST_USERNAME)
        assert target_balance == user_balance

    def test_construct_tx_to_1_recipient(self):
        recipients = ["msisrAMDRbagHmDH1S92A2QK7vXLWXVEkG"]
        values = [3000]

        target_serialization = "0100000001dd68838b415c4e7d52b4c09857f7d241cd46b7a9b6cd1eac134bb2c1877154dd010000006a47304402206717006a00c125efc754e74d36b9564d41137140e980f393a9f69dd0fd13579e02205d8490c203ab07681b1562ef05e217b0e987ff4de38727d30f821505408f4f840121037466113b0be7dbf23c54054648174664d3241c4dd14ebf9a8b1efc949022f0cdffffffff02b80b0000000000001976a91485e2ca0d69906a9b9d79e491af9c0df0dd482bb588ac280a0000000000001976a9141c816105b2d3480a1f7ee8aec327cfda96407cc988ac00000000"

        tx_returns = construct_transaction(recipients, values, TEST_USERNAME)
        tx_obj = tx_returns[0]
        used_utxos = tx_returns[2]
        assert tx_obj.serialize().hex() == target_serialization

        # set utxo of 6000 bitcoin as "spent"
        broadcast_transaction(tx_obj, online=False, self_broadcast='y', needs_change=True, username=TEST_USERNAME, used_utxos=used_utxos)

        new_balance, new_unconfirmed_balance = get_balance(TEST_USERNAME, True)
        assert new_balance == 4000
        assert new_unconfirmed_balance == 2600

        # confirm change output from our transaction
        tx_set_confirmed(TEST_USERNAME, tx_obj.id())

    def test_spend_from_2(self):
        recipients = ["msisrAMDRbagHmDH1S92A2QK7vXLWXVEkG"]
        # the wallet must use both of the utxos in order to construct the transaction
        values = [5000]

        target_serialization = "0100000002bc87747a09fb479784dabebe2f9b4247691b6914c44c016c2dc4fd658d9f025c010000006a4730440220380dc69f3838510ab3a394040c81cc2f1a2d4f354bc008266c3ee6d763cdc6660220661d149cbfb73abaf3c4b5ee44468c71ea658ce58a93629707f35e5d05fe604301210271bacc3bdadfd468ade47751cb9f8701597cd2aee9301060e44852dc1036e17effffffffac77a9f7fb510a7b244c4bfca6270751fc3b301b93bc620d68ecbc434bf0302f010000006b483045022100e6f4dab12c682dffd1268337048061ad9aad262477c2d8e5e22f291ee60d119702201bbdf682e96b975428848882c8444952be8a0dc1e7369e9b2b32ee8945da3de40121027529589f1e161364a1269c33b1b6127bedf283900695942d0c3c1ecfb391c035ffffffff0288130000000000001976a91485e2ca0d69906a9b9d79e491af9c0df0dd482bb588acb0040000000000001976a9142fccd9e8e873afd6b209dc87c566292e3daac7de88ac00000000"

        tx_returns = construct_transaction(recipients, values, TEST_USERNAME)
        tx_obj = tx_returns[0]
        used_utxos = tx_returns[2]

        assert tx_obj.serialize().hex() == target_serialization

        # set utxos bitcoin as "spent"
        broadcast_transaction(tx_obj, online=False, self_broadcast='y', needs_change=True, username=TEST_USERNAME, used_utxos=used_utxos)

        new_balance, new_unconfirmed_balance = get_balance(TEST_USERNAME, True)

        assert new_balance == 0
        assert new_unconfirmed_balance == 1200

        # confirm change output from our transaction
        tx_set_confirmed(TEST_USERNAME, tx_obj.id())

    def test_with_2_recipients(self):

        add_key(TEST_USERNAME, "6a03afdd0e7cbd55d5392d795c83392b6f691a9b8847526322b9e0d2cc67a364","n2JGKD4f9TKdPg62YthhW8Y37C1mT5YSi3")

        add_utxo(TEST_USERNAME, "38db0301a04669b29a57e85e1b3bc73c623073dec7a8f4f666019aa8fa6ca164", 0, 6200, "n2JGKD4f9TKdPg62YthhW8Y37C1mT5YSi3", "OP_DUP OP_HASH160 e3f446b650a7b1558fb6064a8257e40abb5f06a4 OP_EQUALVERIFY OP_CHECKSIG", "0", TXOState.CONFIRMED_UTXO.value)

        recipients = ["msisrAMDRbagHmDH1S92A2QK7vXLWXVEkG", "mu68YHXMEmtcZ1pCLiMv4RLcWbMfWDmEu5"]
        values = [3000, 3900]

        target_serialization = "0100000002cf74d0bb181e42f6bf90428793e2c15ee461759c6a77513355e4e008d2d269f7010000006a4730440220100c7d2dd207bac5cf838c59bab3fad16f4b589ff814415105bcadeb6ae72f0d02205b7d9006440fc4a1b16e74d1839cee6e2fbf20106912e6bd47f92482921140c401210298d2079527e16a8db18f0be65919825c5cddf63e634f2f7693b0813af1c19e29ffffffff64a16cfaa89a0166f6f4a8c7de7330623cc73b1b5ee8579ab26946a00103db38000000006a4730440220551a22d38f45832067d804ca44c59031bc4ea2e7816674c58f3e6323875371150220125f86d36d35d7ea0c1a13ced74a5fdc99dea7aafb58ea72e38b2dd9a379ceb0012102c9925834169f2484406159fdc9c53e74f5e50620909c1891c74debc8a2cbc1e9ffffffff02b80b0000000000001976a91485e2ca0d69906a9b9d79e491af9c0df0dd482bb588ac3c0f0000000000001976a91494dfea11e40cc312bd821a672eacd73567d3166c88ac00000000"

        tx_returns = construct_transaction(recipients, values, TEST_USERNAME)
        tx_obj = tx_returns[0]
        used_utxos = tx_returns[2]

        assert tx_obj.serialize().hex() == target_serialization


        assert str(tx_obj.tx_outs[0].script_pubkey) == "OP_DUP OP_HASH160 85e2ca0d69906a9b9d79e491af9c0df0dd482bb5 OP_EQUALVERIFY OP_CHECKSIG" and tx_obj.tx_outs[0].amount == 3000
        assert str(tx_obj.tx_outs[1].script_pubkey) == "OP_DUP OP_HASH160 94dfea11e40cc312bd821a672eacd73567d3166c OP_EQUALVERIFY OP_CHECKSIG" and tx_obj.tx_outs[1].amount == 3900


        # set utxos bitcoin as "spent"
        broadcast_transaction(tx_obj, online=False, self_broadcast='y', needs_change=False, username=TEST_USERNAME, used_utxos=used_utxos)

        new_balance, new_unconfirmed_balance = get_balance(TEST_USERNAME, True)

        assert new_balance == 0
        assert new_unconfirmed_balance == 0

if __name__ == '__main__':
    unittest.main()
