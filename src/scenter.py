import warnings
warnings.simplefilter("ignore", category=DeprecationWarning)

from web3 import Web3
import argparse
import json
from solc import compile_files
from web3.middleware import geth_poa_middleware
from web3.utils.transactions import wait_for_transaction_receipt
import time
from eth_account import Account

def get_abi(contract_name):
    contract_compiled = compile_files([CONTRACT_DIR + contract_name + '.sol'])[CONTRACT_DIR + contract_name + '.sol:' + contract_name]
    return contract_compiled['abi']

CONTRACT_DIR = './contracts/'

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # parser args
    parser.add_argument('--new')
    parser.add_argument('--reg', action='store_true')
    parser.add_argument('--verify')


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
        try:
            with open('scenter.json') as scenter_file:
                config = json.load(scenter_file)
            actor = w3.toChecksumAddress(config['account'])
            password = config['password']
        except:
            actor = w3.toChecksumAddress(w3.eth.accounts[0])
            password = ''

        if not w3.personal.unlockAccount(actor, password):
            raise RuntimeError('Bad account or password!')

        dev_account = w3.eth.accounts[0]
        # REMOVE BEFORE TEST
        # actor = dev_account

        with open('database.json') as database_file:
            management_address = json.load(database_file)['mgmtContract']

        management_contract = w3.eth.contract(management_address, abi=get_abi('ManagementContract'))

        if args.reg:
            sc_exists = management_contract.functions.serviceCenters(actor).call()
            if not sc_exists:
                tx_hash = management_contract.functions.registerServiceCenter().transact({'from': actor})
                wait_for_transaction_receipt(w3, tx_hash)
                print('Registered successfully')
            else:
                print('Already registered')
        elif args.verify:
            path = args.verify

            with open(path) as src_file:
                privkey_line = src_file.read().split('\n')[0]
                privkey_str = privkey_line.split('=')[1][1:]
                privkey = int(privkey_str).to_bytes(32, 'big')

            json_path = path[:-2]+'json'

            try:
                with open(json_path) as json_file:
                    storage = json.load(json_file)
            except:
                storage = {'n': 0}

            n = storage['n']
            t = int(time.time())
            t = 1522396132

            m = n * 2 ** 32 + t


            m_hash = w3.sha3(m.to_bytes(32, 'big'))

            signed_msg = w3.eth.account.privateKeyToAccount(privkey).sign(m_hash)

            v = signed_msg['v']
            r = signed_msg['r'].to_bytes(32, 'big')
            s = signed_msg['s'].to_bytes(32, 'big')

            with open('database.json') as database_file:
                management_address = json.load(database_file)['mgmtContract']

            management_contract = w3.eth.contract(management_address, abi=get_abi('ManagementContract'))

            battery_management_address = w3.toChecksumAddress(management_contract.functions.batteryManagement().call())
            battery_management_contract = w3.eth.contract(battery_management_address, abi=get_abi('BatteryManagement'))

            response, address = battery_management_contract.functions.verifyBattery(n, t, v, r, s).call()
            vendor_address = battery_management_contract.functions.vendorOf(address).call()

            vendor_id = management_contract.functions.vendors(vendor_address).call()[0]
            vendor_name = management_contract.functions.vendorNames(vendor_id).call()

            _id = Account.recoverMessage(m_hash, vrs=(v, r, s))

            print(n, t, v, r.hex(), s.hex())

            print(_id, address)

            exit(0)

            if response == 0:
                print("Verified successfully.\nTotal charges: %i\nVendor ID: %s\nVendor Name: %s", n, address,
                      vendor_name)
            elif response == 1:
                print("Battery with the same status already replaced. Probably the battery forged.")
            elif response == 2:
                print("Verifiсation failed. Probably the battery forged.")
            elif response == 999:
                print("Verifiсation failed. Probably the battery forged.")
