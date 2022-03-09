## Bitcoin Testnet Wallet - In-Progress, Not A Production Wallet
This is a Bitcoin testnet wallet which can: generate new addresses each time you want to recieve a transaction, synchronize your UTXOs, and constructs raw hex p2pkh transactions which you can broadcast here: https://blockstream.info/testnet/tx/push . 
This wallet utilizes the Bitcoin library from [Programming Bitcoin](https://www.oreilly.com/library/view/programming-bitcoin/9781492031482/) by Jimmy Song, licensed under [CC-BY-NC-ND](https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode), and published by [O'Reilly Media, Inc.March 2019](https://learning.oreilly.com/library/publisher/oreilly-media-inc/). 

### Running The Testnet Wallet
The wallet recieves blocks and transactions in the background whenever the wallet is being used. Run interface.py to start the wallet.Dependencies: requests, base58, and mnemonic (all these can be installed using pip).

### Connecting to A Full Node
You can modify the full node you connect to by using the "change node" command on the wallet and providing it with the full node you would like to connect to.
Note: "peerbloomfilters=1" must be in the bitcoin.conf file of the full node you try to connect to.
