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
        private_key = '0x' + config['key']

        address = w3.eth.account.privateKeyToAccount(private_key).address

        if args.account:
            print(address)


