# install web3 >=4.0.0 by `pip install --upgrade 'web3==4.0.0b11'`
from web3 import Web3, IPCProvider
from web3.middleware import geth_poa_middleware
from web3.utils.transactions import wait_for_transaction_receipt

from json import load, dump, JSONDecodeError
import argparse
import sys, os
import math

from utils import compileContracts, writeDataBase, initializeContractFactory

web3 = Web3()

# configure provider to work with PoA chains
web3.middleware_stack.inject(geth_poa_middleware, layer=0)
try:
    with open('account.json') as file:
        config = load(file)
    actor = web3.toChecksumAddress(config['account'])
    gasPrice = web3.toWei(1, 'gwei')
    txTmpl = {'from': actor, 'gasPrice': gasPrice}
except:
    pass

databaseFile = 'database.json'

try:
    with open(databaseFile) as file:
        database = load(file)
except FileNotFoundError:
    database = {}
except JSONDecodeError:
    database = {}

def unlockAccount(_w3):
    _w3.personal.unlockAccount(actor, config['password'], 300)

contractFileMgmt = './contracts/ManagementContract.sol'
mgmtContractName = 'ManagementContract'

def ManagementContract(_w3):
    _compiled = compileContracts(contractFileMgmt)
    _mgmtContract = initializeContractFactory(_w3, _compiled, contractFileMgmt + ":" + mgmtContractName,
                                              database['mgmtContract'])
    return _mgmtContract

def registerVendor(_w3, _name, _value=1):
    mgmtContract = ManagementContract(_w3)
    tx = txTmpl
    if _value > _w3.eth.getBalance(tx['from']):
        return "Failed. No enough funds to deposit."
    else:
        try:
            tx['value'] = _value
            txHash = mgmtContract.functions.registerVendor(_name.encode()).transact(tx)
            receipt = wait_for_transaction_receipt(_w3, txHash)
            if receipt.status == 1:
                return mgmtContract.events.Vendor().processReceipt(receipt)[0]['args']['tokenId']
        except ValueError:
            return "Failed. The vendor name is not unique."

def regBat(_w3, _count, _value=0):
    _tx = txTmpl
    _tx['value'] = _value
    _batkeys = []
    _args = []
    
    for i in range(_count):
        _privKey = _w3.sha3(os.urandom(20))
        _batkeys.append((_privKey, _w3.eth.account.privateKeyToAccount(_privKey).address))
    for i in range(len(_batkeys)):
        _args.append(_w3.toBytes(hexstr=_batkeys[i][1]))

    mgmtContract = ManagementContract(_w3)
    txHash = mgmtContract.functions.registerBatteries(_args).transact(_tx)
    receipt = wait_for_transaction_receipt(_w3, txHash)
    result = receipt.status
    form = 'Created battery with ID: {}'
    if result >= 1:
        for batId in _batkeys:
            print(form.format(delHexPrefix(batId[1]).lower()))
    else:
        print('Batteries registration failed')

def delHexPrefix(_s: str):
    if _s[:2] == '0x':
        _s = _s[2:]
    return _s

def create_parser():
    parser = argparse.ArgumentParser(
        description='Battery vendor management tool',
        epilog="""
It is expected that Web3 provider specified by WEB3_PROVIDER_URI
environment variable. E.g.
WEB3_PROVIDER_URI=file:///path/to/node/rpc-json/file.ipc
WEB3_PROVIDER_URI=http://192.168.1.2:8545
"""
    )

    parser.add_argument(
        '--new', nargs=1, required=False,
        help='Add address to the account.json'
    )

    parser.add_argument(
        '--reg', nargs=2, required=False,
        help='Register a vendor'
    )
    parser.add_argument(
        '--bat', nargs="+", required=False,
        help='Register batteries'
    )

    return parser


def main():
    parser = create_parser()

    args = parser.parse_args()

    if args.new:
        global database
        database = {}
        database['account'] = web3.personal.newAccount(args.new[0])
        database['password'] = args.new[0]
        if len(database['account']) == 42:
            writeDataBase(database, 'account.json')
            print('{}'.format(database['account']))
        else:
            sys.exit("Cannot get address")
    elif args.reg:
        if 'mgmtContract' in database:
            unlockAccount(web3)
            result = registerVendor(web3, args.reg[0], web3.toWei(args.reg[1], 'ether'))
            if isinstance(result, bytes):
                print('Success.\nVendor ID: {}'.format(delHexPrefix(web3.toHex(result))))
            else:
                sys.exit(result)
        else:
            sys.exit("Management contract address not found in the database")
    elif args.bat:
        if 'mgmtContract' in database:
            unlockAccount(web3)
            if len(args.bat) > 1:
                result = regBat(web3, int(args.bat[0]), web3.toWei(args.bat[1], 'ether'))
            else:
                result = regBat(web3, int(args.bat[0]))
        else:
            sys.exit("Management contract address not found in the database")
    else:
        sys.exit("No parameters provided")

if __name__ == '__main__':
    main()
