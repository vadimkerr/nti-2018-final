import warnings

warnings.simplefilter("ignore", category=DeprecationWarning)

# install web3 >=4.0.0 by `pip install --upgrade 'web3==4.0.0b11'`
from web3 import Web3
from web3.middleware import geth_poa_middleware
from web3.utils.transactions import wait_for_transaction_receipt

import datetime as dt
from random import randint

import argparse
import sys

from utils import writeDataBase, openDataBase, getActualGasPrice, compileContracts, initializeContractFactory

web3 = Web3()

# configure provider to work with PoA chains
web3.middleware_stack.inject(geth_poa_middleware, layer=0)

accountDatabaseName = 'car.json'
mgmtContractDatabaseName = 'database.json'

gasPrice = getActualGasPrice(web3)

registrationRequiredGas = 50000

# contract files
contracts = {'mgmt':   ('contracts/ManagementContract.sol', 'ManagementContract')}

def _createCarAccountDatabase(_carPrivateKey):
    data = {'key': _carPrivateKey}
    writeDataBase(data, accountDatabaseName)

# generate private key using current time and random int
def _generatePrivateKey():
    t = int(dt.datetime.utcnow().timestamp())
    k = randint(0, 2 ** 16)
    privateKey = web3.toHex(web3.sha3((t + k).to_bytes(32, 'big')))
    return _delHexPrefix(privateKey)

# delete hex prefix from string
def _delHexPrefix(_s: str):
    if _s[:2] == '0x':
        _s = _s[2:]
    return _s

def new():
        privateKey = _generatePrivateKey()
        data = {"key": privateKey}
        writeDataBase(data, accountDatabaseName)
        print(web3.eth.account.privateKeyToAccount(data['key']).address)

def account():
    data = openDataBase(accountDatabaseName)
    if data is None:
        print("Cannot access account database")
        return

    privKey = data['key']
    print(web3.eth.account.privateKeyToAccount(privKey).address)

def reg():
    data = openDataBase(mgmtContractDatabaseName)
    if data is None:
        print("Cannot access management contract database")
        return

    mgmtContractAddress = data['mgmtContract']

    data = openDataBase(accountDatabaseName)
    if data is None:
        print("Cannot access account database")
        return

    privateKey = data['key']

    compiledContract = compileContracts(contracts['mgmt'][0])
    mgmtContract = initializeContractFactory(web3, compiledContract, contracts['mgmt'][0] + ':' + contracts['mgmt'][1],
                                             mgmtContractAddress)

    carAddress = web3.eth.account.privateKeyToAccount(privateKey).address

    if registrationRequiredGas * gasPrice > web3.eth.getBalance(carAddress):
        print("No enough funds to send transaction")
        return

    nonce = web3.eth.getTransactionCount(carAddress)
    tx = {'gasPrice': gasPrice, 'nonce': nonce}

    regTx = mgmtContract.functions.registerCar().buildTransaction(tx)
    signTx = web3.eth.account.signTransaction(regTx, privateKey)
    txHash = web3.eth.sendRawTransaction(signTx.rawTransaction)
    receipt = wait_for_transaction_receipt(web3, txHash)

    if receipt.status == 1:
        print('Registered successfully')
    else:
        print('Already registered')

def create_parser():
    parser = argparse.ArgumentParser(
        description='Autonomous Ground Vehicle software',
        epilog="""
    It is expected that Web3 provider specified by WEB3_PROVIDER_URI
    environment variable. E.g.
    WEB3_PROVIDER_URI=file:///path/to/node/rpc-json/file.ipc
    WEB3_PROVIDER_URI=http://192.168.1.2:8545
    """
    )

    parser.add_argument(
        '--new', action='store_true', required=False,
        help='Generate a new account for the particular AGV'
    )

    parser.add_argument(
        '--account', action='store_true', required=False,
        help='Get identificator (Ethereum address) of AGV from the private key stored in car.json'
    )

    parser.add_argument(
        '--reg', action='store_true', required=False,
        help='Register the vehicle in the chain'
    )

    return parser

def main():
    parser = create_parser()
    args = parser.parse_args()

    if args.new:
        new()
    elif args.account:
        account()
    elif args.reg:
        reg()
    else:
        sys.exit("No parameters provided")


if __name__ == '__main__':
    main()
