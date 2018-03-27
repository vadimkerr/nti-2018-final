import warnings
warnings.simplefilter("ignore", category=DeprecationWarning)

import web3
from web3 import Web3
import argparse
import json
from solc import compile_files
from web3.middleware import geth_poa_middleware
from random import randint

CONTRACT_DIR = './contracts/'


def str_to_bytes(value):
    if isinstance(value, bytearray):
        value = bytes(value)
    if isinstance(value, bytes):
        return value
    return bytes(value, 'utf-8')

def get_abi(contract_name):
    contract_compiled = compile_files([CONTRACT_DIR + contract_name + '.sol'])[CONTRACT_DIR + contract_name + '.sol:' + contract_name]
    return contract_compiled['abi']

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # parser args
    parser.add_argument('--new')
    parser.add_argument('--reg', nargs=2)
    parser.add_argument('--bat')


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
        actor = dev_account

        with open('database.json') as database_file:
            management_address = json.load(database_file)['mgmtContract']

        management_contract = w3.eth.contract(management_address, abi=get_abi('ManagementContract'))

        if args.reg:
            vendor_name = str_to_bytes(args.reg[0])
            fee = int(float(args.reg[1]) * (10 ** 18))

            battery_fee = management_contract.functions.batteryFee().call()

            if fee >= battery_fee * 1000:
                tx_hash = management_contract.functions.registerVendor(vendor_name).transact({'from': actor, 'value': fee})

                receipt = w3.eth.getTransactionReceipt(tx_hash)
                new_vendor_id = management_contract.events.Vendor().processReceipt(receipt)[0]['args']['']

                print('Success.')
                print('Vendor ID: ' + w3.toHex(new_vendor_id)[2:].lower())
            else:
                print('Failed. Payment is low.')

        elif args.bat:
            batteries_number = int(args.bat)

            batteries = []
            for i in range(batteries_number):
                new_private_key = randint(0, 2**256-1).to_bytes(32, 'big')
                new_battery_id = w3.eth.account.privateKeyToAccount(new_private_key).address[2:]

                batteries.append(new_battery_id)

            battery_fee = management_contract.functions.batteryFee().call()
            management_contract.functions.registerBatteries(batteries).transact({'from': actor, 'value': battery_fee * batteries_number})
