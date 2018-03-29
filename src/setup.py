import warnings

warnings.simplefilter("ignore", category=DeprecationWarning)

# install web3 >=4.0.0 by `pip install --upgrade 'web3==4.0.0b11'`
from web3 import Web3
from web3.middleware import geth_poa_middleware
from web3.utils.transactions import wait_for_transaction_receipt

from web3.utils.threads import (
    Timeout,
)
from random import random

import argparse
import sys

from utils import createNewAccount, writeDataBase, openDataBase, unlockAccount, getActualGasPrice
from utils import compileContracts, initializeContractFactory

web3 = Web3()

# configure provider to work with PoA chains
web3.middleware_stack.inject(geth_poa_middleware, layer=0)

accountDatabaseName = 'account.json'
mgmtContractDatabaseName = 'database.json'

gasPrice = getActualGasPrice(web3)

# contract files
contracts = {'token':  ('contracts/ERC20Token.sol', 'ERC20Token'),
             'wallet': ('contracts/ServiceProviderWallet.sol', 'ServiceProviderWallet'),
             'mgmt':   ('contracts/ManagementContract.sol', 'ManagementContract'),
             'battery':('contracts/BatteryManagement.sol', 'BatteryManagement')}

def _deployContractAndWait(_actor, _contrSourceFile, _contractName, args=None):
    txHash = _deployContract(_actor, _contrSourceFile, _contractName, args)
    receipt = wait_for_transaction_receipt(web3, txHash)
    return receipt.contractAddress

def _deployContract(_actor, _contrSourceFile, _contractName, args=None):
    compiled = compileContracts(_contrSourceFile)
    contract = initializeContractFactory(web3, compiled, _contrSourceFile + ":" + _contractName)
    
    tx = {'from': _actor, 'gasPrice': gasPrice}

    return contract.deploy(transaction=tx, args=args)

def _waitForValidation(_w3, _txdict, _tmout=120):
    receiptslist = {}
    for i in list(_txdict):
        receiptslist[i] = [_txdict[i], None]
    confirmations = len(list(_txdict))
    
    with Timeout(_tmout) as timeout:
        while (confirmations > 0):
            for i in list(_txdict):
                if receiptslist[i][1] is None:
                    txn_receipt = _w3.eth.getTransactionReceipt(receiptslist[i][0])
                    if txn_receipt is not None:
                        receiptslist[i][1] = txn_receipt
                        confirmations = confirmations - 1
                timeout.sleep(random())

    return receiptslist

def _createMgmtContractDatabase(_contractAddress):
    data = {'mgmtContract': _contractAddress}
    writeDataBase(data, mgmtContractDatabaseName)

def setup(_serviceFee):
    serviceFee = web3.toWei(_serviceFee, 'ether')
    
    data = openDataBase(accountDatabaseName)
    if data is None:
        print("Cannot access account database")
        return

    actor = data["account"]

    unlockAccount(web3, actor, data["password"])

    # deploy token and wallet in one block (hopefully)
    txd = {}
    for i in ['token', 'wallet']:
        txd[i] = _deployContract(actor, contracts[i][0], contracts[i][1])

    # wait for deployment transactions validation
    receiptd = _waitForValidation(web3, txd)

    currencyTokenContractAddress = receiptd['token'][1].contractAddress
    serviceProviderWalletAddress = receiptd['wallet'][1].contractAddress
    
    if (receiptd['token'][1] is not None) and (receiptd['wallet'][1] is not None):
        serviceProviderWalletAddress = receiptd['wallet'][1].contractAddress
        currencyTokenContractAddress = receiptd['token'][1].contractAddress
    
        if serviceProviderWalletAddress is not None: 
            # deploy management contract
            mgmtContractAddress = _deployContractAndWait(actor, contracts['mgmt'][0], contracts['mgmt'][1],
                                                         [serviceProviderWalletAddress, serviceFee])

            if mgmtContractAddress is not None:
                _createMgmtContractDatabase(mgmtContractAddress)
                
                # deploy battery management
                batteryMgmtContractAddress = _deployContractAndWait(actor, contracts['battery'][0], contracts['battery'][1],
                                                                    [mgmtContractAddress, currencyTokenContractAddress])
                
                if batteryMgmtContractAddress is not None:
                    compiledContract = compileContracts(contracts['mgmt'][0])
                    mgmtContract = initializeContractFactory(web3, compiledContract,
                                                              contracts['mgmt'][0]+':'+contracts['mgmt'][1],
                                                              mgmtContractAddress)
                    txHash = mgmtContract.functions.setBatteryManagementContract(batteryMgmtContractAddress).transact({'from': actor, 'gasPrice': gasPrice})
                    receipt = wait_for_transaction_receipt(web3, txHash)

                    if receipt.status == 1:
                        print('Management contract:', mgmtContractAddress, sep=' ')
                        print('Wallet contract:', serviceProviderWalletAddress, sep=' ')
                        print('Currency contract:', currencyTokenContractAddress, sep=' ')

                        return
    print('Contracts deployment and configuration failed')

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
        help='Add account for software development company'
    )

    parser.add_argument(
        '--setup', type=float, required=False,
        help='Deploy contract(s) to the chain. Set fee (in ether) for registration of one battery, which reflects vendor registration fee'
    )
    
    return parser

def main():
    parser = create_parser()
    args = parser.parse_args()

    if args.new:
        print(createNewAccount(web3, args.new, accountDatabaseName))
    elif args.setup:
        setup(args.setup)
    else:
        sys.exit("No parameters provided")

if __name__ == '__main__':
    main()
