import warnings
warnings.simplefilter("ignore", category=DeprecationWarning)

from web3 import Web3
import argparse
import json
from solc import compile_files
from web3.middleware import geth_poa_middleware
from web3.utils.transactions import wait_for_transaction_receipt

CONTRACT_DIR = './contracts/'


def get_abi(contract_name):
    contract_compiled = compile_files([CONTRACT_DIR + contract_name + '.sol'])[CONTRACT_DIR + contract_name + '.sol:' + contract_name]
    return contract_compiled['abi']


def deploy_contract(w3, contract_name, account, args=None):
    contract_compiled = compile_files([CONTRACT_DIR + contract_name + '.sol'])[CONTRACT_DIR + contract_name + '.sol:' + contract_name]
    contract = w3.eth.contract(abi=contract_compiled['abi'], bytecode=contract_compiled['bin'])

    tx_hash = contract.deploy(args=args, transaction={'from': account})
    tx_receipt = wait_for_transaction_receipt(w3, tx_hash)

    contract_address = tx_receipt['contractAddress']

    return contract_address


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # parser args
    parser.add_argument('--new')
    parser.add_argument('--setup')
    parser.add_argument('--setfee')

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

        if args.setup:
            service_fee = int(float(args.setup) * (10 ** 18))

            # deploy ERC20 token
            erc20_address = deploy_contract(w3, 'ERC20', actor)

            # deploy ServiceProviderWallet
            spw_address = deploy_contract(w3, 'ServiceProviderWallet', actor)

            # deploy ManagementContract
            mgmt_address = deploy_contract(w3, 'ManagementContract', actor, [spw_address, service_fee])

            # deploy BatteryManagement
            bmgmt_address = deploy_contract(w3, 'BatteryManagement', actor, [mgmt_address, erc20_address])

            management_contract = w3.eth.contract(mgmt_address, abi=get_abi('ManagementContract'))
            tx_hash = management_contract.functions.setBatteryManagementContract(bmgmt_address).transact({'from': actor})
            wait_for_transaction_receipt(w3, tx_hash)

            with open('database.json', 'w') as database_file:
                json.dump({'mgmtContract': mgmt_address}, database_file)

            print('Management contract: ' + mgmt_address)
            print('Wallet contract: ' + spw_address)
            print('Currency contract: ' + erc20_address)

        elif args.setfee:
            new_fee = int(float(args.setfee) * (10 ** 18))

            with open('database.json') as database_file:
                management_address = json.load(database_file)['mgmtContract']

            management_contract = w3.eth.contract(management_address, abi=get_abi('ManagementContract'))

            owner = management_contract.functions.owner().call()
            if actor == owner:
                tx_hash = management_contract.functions.setFee(new_fee).transact({'from': actor})
                wait_for_transaction_receipt(w3, tx_hash)
                print('Updated successfully')
            else:
                print('No permissions to change the service fee')
