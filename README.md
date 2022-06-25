## Bitcoin Testnet Wallet - In-Progress, Not A Production Wallet
This is a Bitcoin Testnet wallet which I use to implement Bitcoin concepts as I learn about them.
This wallet utilizes the Bitcoin library from [Programming Bitcoin](https://www.oreilly.com/library/view/programming-bitcoin/9781492031482/) by Jimmy Song, licensed under [CC-BY-NC-ND](https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode), and published by [O'Reilly Media, Inc.March 2019](https://learning.oreilly.com/library/publisher/oreilly-media-inc/). 

### Features
Overtime I've implemented the following features in this wallet:
- sending and receiving to p2pkh addresses
- broadcasting transactions from the node, receiving transactions and updating balance, some reorg safety(especially because reorgs are larger and more frequent on the testnet)
- non-hardened child key derivation, so basically implementing part of [BIP-32](https://github.com/bitcoin/bips/blob/master/bip-0032.mediawiki)
- sending to segwit version 0 addresses
- additional functionality when wallet is offline or not fully synchronized, basically an "offline mode"

In-Progress:
- receiving to segwit version 0 addresses
- make coin selection not SFFO any more, and use effective value when selecting
- More detailed error messages and more logging
- RBF([BIP-125](https://github.com/bitcoin/bips/blob/master/bip-0125.mediawiki))

### References
Places I referred to when implementing certain parts of the wallet:
- [Bitcoin Core](https://github.com/bitcoin/bitcoin)
- [buidl-python](https://github.com/buidl-bitcoin/buidl-python/blob/main/LICENSE.md)
- [bitcoinlib](https://github.com/1200wd/bitcoinlib)

### Running The Testnet Wallet
The wallet recieves blocks and transactions in the background whenever the wallet is being used. Run cli.py to start the wallet. Dependencies: requests, base58, and mnemonic (all these can be installed using pip).

### Connecting to A Full Node
You can modify the full node you connect to by using the `change node` command on the wallet and providing it with the full node you would like to connect to.
Note: "peerbloomfilters=1" must be in the bitcoin.conf file of the full node you try to connect to.
