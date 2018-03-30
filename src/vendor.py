import warnings
warnings.simplefilter("ignore", category=DeprecationWarning)

from web3 import Web3
import argparse
import json
from solc import compile_files
from web3.middleware import geth_poa_middleware
from random import randint
from binascii import unhexlify
from web3.utils.transactions import wait_for_transaction_receipt
import os


def format_number(num):
    if num % 1:
        return str(num).rstrip('0').rstrip('.')

    return str(int(num))


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
    parser.add_argument('--bat', nargs='+')
    parser.add_argument('--regfee', action='store_true')
    parser.add_argument('--batfee', action='store_true')
    parser.add_argument('--deposit', action='store_true')
    parser.add_argument('--owner', nargs=2)

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

        with open('database.json') as database_file:
            management_address = json.load(database_file)['mgmtContract']

        management_contract = w3.eth.contract(management_address, abi=get_abi('ManagementContract'))

        if args.reg:
            vendor_name = str_to_bytes(args.reg[0])
            fee = int(float(args.reg[1]) * (10 ** 18))

            # checking if address is unique
            unique_address = management_contract.functions.isUnique().call({'from': actor})
            if not unique_address:
                print('Failed. The vendor address already used.')
                exit(0)

            # checking if name is unique
            not_unique_name = management_contract.functions.isNameUnique(vendor_name).call()
            if not_unique_name:
                print('Failed. The vendor name is not unique.')
                exit(0)


            # registration
            battery_fee = management_contract.functions.batteryFee().call()

            if fee >= battery_fee * 1000:
                try:
                    tx_hash = management_contract.functions.registerVendor(vendor_name).transact({'from': actor, 'value': fee})
                except:
                    print('Failed. No enough funds to deposit.')
                    exit(0)

                receipt = wait_for_transaction_receipt(w3, tx_hash)
                new_vendor_id = management_contract.events.Vendor().processReceipt(receipt)[0]['args']['']

                print('Success.')
                print('Vendor ID: ' + w3.toHex(new_vendor_id)[2:].lower())
            else:
                print('Failed. Payment is low.')

        elif args.bat:
            batteries_number = int(args.bat[0])

            if len(args.bat) > 1:
                additional_deposit = int(float(args.bat[1]) * (10 ** 18))
            else:
                additional_deposit = 0

            available_deposit = management_contract.functions.vendorDeposit(actor).call()

            battery_fee = management_contract.functions.batteryFee().call()

            if available_deposit > battery_fee * batteries_number:
                batteries = []
                private_keys = []
                for i in range(batteries_number):
                    new_private_key = randint(0, 2 ** 256 - 1).to_bytes(32, 'big')
                    new_battery_id = w3.eth.account.privateKeyToAccount(new_private_key).address[2:]
                    new_battery_id = unhexlify(new_battery_id)
                    batteries.append(new_battery_id)
                    private_keys.append(new_private_key)

                # create firmware files
                if not os.path.exists('firmware'):
                    os.makedirs('firmware')

                for i in range(batteries_number):
                    filename = w3.toHex(batteries[i])[2:10]
                    code = '_privkey = ' + str(int.from_bytes(private_keys[i], byteorder='big'))

                    code += '''\nimport web3
import json
import argparse
import time

w3 = web3.Web3()
storage_name = w3.eth.account.privateKeyToAccount(_privkey).address[2:10].lower()

parser = argparse.ArgumentParser()
# parser args
parser.add_argument('--charge', action='store_true')
parser.add_argument('--get', action='store_true')

args = parser.parse_args()

try:
    with open(storage_name + '.json') as storage_file:
        storage = json.load(storage_file)
except:
    storage = {'n': 0}

if args.charge:
    storage['n'] += 1

    with open(storage_name + '.json', 'w') as storage_file:
        json.dump(storage, storage_file)
        storage_file.close()

elif args.get:
    n = storage['n']
    t = int(time.time())

    m = n * 2**32 + t

    signed_msg = w3.eth.account.privateKeyToAccount(_privkey).sign(m)

    print(n)
    print(t)
    print(signed_msg['v'])
    print(hex(signed_msg['r'])[2:])
    print(hex(signed_msg['s'])[2:])
'''

                    with open('firmware/'+filename+'.py', 'w') as firmware_file:
                        firmware_file.write(code)

                # WILL NOT WORK WITH GREAT NUMBER OF BATTERIES!!!
                tx_hash = management_contract.functions.registerBatteries(batteries).transact({'from': actor, 'value': additional_deposit})
                wait_for_transaction_receipt(w3, tx_hash)
                for battery_id in batteries:
                    print('Created battery with ID: ' + w3.toHex(battery_id)[2:])
            else:
                print('Failed. No enough funds to register object.')
        elif args.regfee:
            fee = int(management_contract.functions.registrationDeposit().call()) / (10 ** 18)

            print('Vendor registration fee: ' + format_number(fee))
        elif args.batfee:
            battery_fee = int(management_contract.functions.batteryFee().call({'from': actor})) / (10 ** 18)

            print('Production fee per one battery: ' + format_number(battery_fee))
        elif args.deposit:
            vendor_id = management_contract.functions.vendorId(actor).call()
            if vendor_id == b'\x00\x00\x00\x00':
                print('Vendor account is not registered.')
                exit(0)

            deposit = int(management_contract.functions.vendorDeposit(actor).call()) / (10 ** 18)

            print('Deposit: ' + format_number(deposit))
        elif args.owner:
            battery_id = args.owner[0]
            new_owner = w3.toChecksumAddress(args.owner[1])

            battery_management_address = w3.toChecksumAddress(management_contract.functions.batteryManagement().call())
            battery_management_contract = w3.eth.contract(battery_management_address, abi=get_abi('BatteryManagement'))

            battery_id = unhexlify(battery_id)

            owner = battery_management_contract.functions.ownerOf(battery_id).call()

            if actor == owner:
                tx_hash = battery_management_contract.functions.transfer(new_owner, battery_id).transact({'from': actor})
                wait_for_transaction_receipt(w3, tx_hash)

                print('Success')
            else:
                print('Failed. Not allowed to change ownership.')