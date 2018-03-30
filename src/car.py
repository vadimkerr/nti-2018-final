import warnings
warnings.simplefilter("ignore", category=DeprecationWarning)

from random import randint
from web3 import Web3
import argparse
import json
from solc import compile_files
from web3.middleware import geth_poa_middleware
from web3.utils.transactions import wait_for_transaction_receipt
import time


def get_abi(contract_name):
    contract_compiled = compile_files([CONTRACT_DIR + contract_name + '.sol'])[CONTRACT_DIR + contract_name + '.sol:' + contract_name]
    return contract_compiled['abi']


def transfer(w3, privkey, to, value, data):
    address = w3.eth.account.privateKeyToAccount(privkey).address

    tx_dict = {
        'nonce': w3.eth.getTransactionCount(address),
        'to': to,
        'value': value,
        'data': data,
        'gas': 100000,
        'gasPrice': int(w3.eth.gasPrice),
        'chainId': int(w3.admin.nodeInfo.protocols.eth.config.chainId)
    }

    raw_tx = w3.eth.account.signTransaction(tx_dict, privkey)['rawTransaction']

    tx_hash = w3.eth.sendRawTransaction(raw_tx)
    tx_hash = Web3.toHex(tx_hash)

    wait_for_transaction_receipt(w3, tx_hash)

    return tx_hash

CONTRACT_DIR = './contracts/'

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # parser args
    parser.add_argument('--new', action='store_true')
    parser.add_argument('--account', action='store_true')
    parser.add_argument('--reg', action='store_true')
    parser.add_argument('--verify')

    args = parser.parse_args()

    w3 = Web3()
    # configure provider to work with PoA chains
    w3.middleware_stack.inject(geth_poa_middleware, layer=0)

    if args.verify:
        path = args.verify

        with open(path) as src_file:
            privkey_line = src_file.read().split('\n')[0]
            privkey_str = privkey_line.split('=')[1][1:]
            privkey = int(privkey_str).to_bytes(32, 'big')

        json_path = path[:-2] + 'json'

        try:
            with open(json_path) as json_file:
                storage = json.load(json_file)
        except:
            storage = {'n': 0}

        n = storage['n']
        t = int(time.time())

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

        vendor_id = management_contract.functions.vendors(address).call()[0]
        vendor_name = management_contract.functions.vendorNames(vendor_id).call()

        if response == 0:
            print("Verified successfully.\nTotal charges: %i\nVendor ID: %s\nVendor Name: %s" % (
            n, vendor_id.hex(), vendor_name.decode()))
        elif response == 1:
            print("Battery with the same status already replaced. Probably the battery forged.")
        elif response == 2:
            print("Verifiсation failed. Probably the battery forged.")
        elif response == 999:
            print("Verifiсation failed. Probably the battery forged.")

    if args.new:
        private_key = w3.toHex(randint(0, 2 ** 256 - 1).to_bytes(32, 'big'))
        address = w3.personal.importRawKey(private_key, '1234')

        with open('car.json', 'w') as car_file:
            json.dump({'key': private_key[2:]}, car_file)

        print(address)
    else:
        with open('car.json') as car_file:
            config = json.load(car_file)
        private_key = config['key']
        address = w3.eth.account.privateKeyToAccount(private_key).address

        if args.account:
            print(address)
        else:
            with open('database.json') as database_file:
                management_address = json.load(database_file)['mgmtContract']

            management_contract = w3.eth.contract(management_address, abi=get_abi('ManagementContract'))

            if args.reg:
                car_exists = management_contract.functions.cars(address).call()
                if not car_exists:
                    data = Web3.sha3(text='registerCar()')[:4]

                    transfer(w3, private_key, management_address, 0, data)
                    print('Registered successfully')
                else:
                    print('Already registered')
