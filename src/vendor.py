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


def format_number(num):
    return str(num).rstrip('0').rstrip('.')


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

            # checking if name unique or not
            event_signature_hash = w3.toHex(w3.sha3(text="NewName(bytes)"))
            event_filter = w3.eth.filter({"address": management_address, 'topics': [event_signature_hash]})

            for log_entry in event_filter.get_all_entries():
                tx_hash = log_entry['transactionHash']
                receipt = wait_for_transaction_receipt(w3, tx_hash)
                registered_vendor = management_contract.events.NewName().processReceipt(receipt)[0]['args']['']

                if registered_vendor == vendor_name:
                    print('Failed. The vendor name is not unique.')
                    exit(0)

            # registration
            battery_fee = management_contract.functions.batteryFee().call()

            if fee >= battery_fee * 1000:
                tx_hash = management_contract.functions.registerVendor(vendor_name).transact({'from': actor, 'value': fee})

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
                for i in range(batteries_number):
                    new_private_key = randint(0, 2 ** 256 - 1).to_bytes(32, 'big')
                    new_battery_id = w3.eth.account.privateKeyToAccount(new_private_key).address[2:]
                    new_battery_id = unhexlify(new_battery_id)
                    batteries.append(new_battery_id)

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