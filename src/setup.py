import warnings
warnings.simplefilter("ignore", category=DeprecationWarning)

from web3 import Web3
import argparse
import json
from solc import compile_files
from web3.middleware import geth_poa_middleware

CONTRACT_DIR = './contracts/'


def deploy_contract(contract_name, account, args=[]):
    contract_compiled = compile_files([CONTRACT_DIR + contract_name + '.sol'])[CONTRACT_DIR + contract_name + '.sol:' + contract_name]
    contract = w3.eth.contract(abi=contract_compiled['abi'], bytecode=contract_compiled['bin'])

    tx_hash = contract.deploy(args=args, transaction={'from': account})
    tx_receipt = w3.eth.getTransactionReceipt(tx_hash)
    contract_address = tx_receipt['contractAddress']

    return contract_address

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # parser args
    parser.add_argument('--new')
    parser.add_argument('--setup')

    args = parser.parse_args()

    w3 = Web3()
    # configure provider to work with PoA chains
    w3.middleware_stack.inject(geth_poa_middleware, layer=0)

    if args.new:
        password = args.new

        new_account = w3.personal.newAccount(password)
        account_info = {
            'account': new_account,
            'password': password
        }
        with open('account.json', 'w') as account_file:
            json.dump(account_info, account_file)
        print(new_account)
    else:
        with open('account.json') as account_file:
            config = json.load(account_file)
        actor = w3.toChecksumAddress(config['account'])
        password = config['password']

        if not w3.personal.unlockAccount(actor, password):
            raise RuntimeError('Bad account or password!')

        dev_account = w3.eth.accounts[0]
        # REMOVE BEFORE TEST
        # actor = dev_account

        if args.setup:
            service_fee = int(float(args.setup) * (10 ** 18))

            # deploy ServiceProviderWallet
            spw_address = deploy_contract('ServiceProviderWallet', actor)

            # deploy ManagementContract
            mgmt_address = deploy_contract('ManagementContract', actor, [spw_address, service_fee])

            # deploy ERC20 token
            erc20_address = deploy_contract('ERC20', actor)

            # deploy BatteryManagement
            bmgmt_address = deploy_contract('BatteryManagement', actor, [mgmt_address, erc20_address])

            with open('database.json', 'w') as database_file:
                json.dump({'mgmtContract': mgmt_address}, database_file)

            print('Management contract: ' + mgmt_address)
            print('Wallet contract: ' + spw_address)
            print('Currency contract: ' + bmgmt_address)