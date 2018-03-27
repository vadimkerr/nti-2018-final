import warnings
warnings.simplefilter("ignore", category=DeprecationWarning)

from web3 import Web3
import argparse
import json
from solc import compile_files
from web3.middleware import geth_poa_middleware


def get_abi(contract_name):
    contract_compiled = compile_files([CONTRACT_DIR + contract_name + '.sol'])[CONTRACT_DIR + contract_name + '.sol:' + contract_name]
    return contract_compiled['abi']

CONTRACT_DIR = './contracts/'

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # parser args
    parser.add_argument('--new')
    parser.add_argument('--reg', action='store_true')


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
        with open('scenter.json', 'w') as account_file:
            json.dump(account_info, account_file)
        print(new_account)
    else:
        with open('scenter.json') as scenter_file:
            config = json.load(scenter_file)
        actor = w3.toChecksumAddress(config['account'])
        password = config['password']

        if not w3.personal.unlockAccount(actor, password):
            raise RuntimeError('Bad account or password!')

        dev_account = w3.eth.accounts[0]
        # REMOVE BEFORE TEST
        actor = dev_account

        with open('database.json') as database_file:
            management_address = json.load(database_file)['mgmtContract']

        management_contract = w3.eth.contract(management_address, abi=get_abi('ManagementContract'))

        if args.reg:
            sc_exists = management_contract.functions.serviceCenters(actor).call()
            if not sc_exists:
                management_contract.functions.registerServiceCenter().transact({'from': actor})
                print('Registered successfully')
            else:
                print('Already registered')