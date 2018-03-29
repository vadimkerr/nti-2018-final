import warnings

warnings.simplefilter("ignore", category=DeprecationWarning)

# install web3 >=4.0.0 by `pip install --upgrade 'web3==4.0.0b11'`
from web3 import Web3
from web3.middleware import geth_poa_middleware
from web3.utils.transactions import wait_for_transaction_receipt

import argparse
import sys

from utils import createNewAccount, openDataBase, unlockAccount, getActualGasPrice
from utils import compileContracts, initializeContractFactory

web3 = Web3()

# configure provider to work with PoA chains
web3.middleware_stack.inject(geth_poa_middleware, layer=0)

accountDatabaseName = 'scenter.json'
mgmtContractDatabaseName = 'database.json'

gasPrice = getActualGasPrice(web3)

registrationRequiredGas = 50000

# contract files
contracts = {'mgmt':   ('contracts/ManagementContract.sol', 'ManagementContract')}

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

    actor = data["account"]

    tx = {'from': actor, 'gasPrice': gasPrice}

    compiledContract = compileContracts(contracts['mgmt'][0])
    mgmtContract = initializeContractFactory(web3, compiledContract, contracts['mgmt'][0] + ':' + contracts['mgmt'][1],
                                             mgmtContractAddress)

    if registrationRequiredGas * gasPrice > web3.eth.getBalance(actor):
        print("No enough funds to send transaction")
        return

    unlockAccount(web3, actor, data["password"])

    try:
        txHash = mgmtContract.functions.registerServiceCenter().transact(tx)
    except ValueError:
        print("Already registered")
        return

    receipt = wait_for_transaction_receipt(web3, txHash)
    if receipt.status == 1:
        print("Registered successfully")

def create_parser():
    parser = argparse.ArgumentParser(
        description='Service provider tool',
        epilog="""
    It is expected that Web3 provider specified by WEB3_PROVIDER_URI
    environment variable. E.g.
    WEB3_PROVIDER_URI=file:///path/to/node/rpc-json/file.ipc
    WEB3_PROVIDER_URI=http://192.168.1.2:8545
    """
    )

    parser.add_argument(
        '--new', type=str, required=False,
        help='Add new service scenter account'
    )

    parser.add_argument(
        '--reg', action='store_true', required=False,
        help='Register service scenter in the chain'
    )

    return parser

def main():
    parser = create_parser()
    args = parser.parse_args()

    if args.new:
        print(createNewAccount(web3, args.new, accountDatabaseName))
    elif args.reg:
        reg()
    else:
        sys.exit("No parameters provided")

if __name__ == '__main__':
    main()
