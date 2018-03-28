import warnings
warnings.simplefilter("ignore", category=DeprecationWarning)

from random import randint
from web3 import Web3
import argparse
import json
from solc import compile_files
from web3.middleware import geth_poa_middleware


def get_abi(contract_name):
    contract_compiled = compile_files([CONTRACT_DIR + contract_name + '.sol'])[CONTRACT_DIR + contract_name + '.sol:' + contract_name]
    return contract_compiled['abi']


def transfer(w3, privkey, to, value, data):
    address = w3.eth.account.privateKeyToAccount(privkey).address

    print(privkey, address, to)

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
    return tx_hash

CONTRACT_DIR = './contracts/'

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # parser args
    parser.add_argument('--new', action='store_true')
    parser.add_argument('--account', action='store_true')
    parser.add_argument('--reg', action='store_true')

    args = parser.parse_args()

    w3 = Web3()
    # configure provider to work with PoA chains
    w3.middleware_stack.inject(geth_poa_middleware, layer=0)

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
