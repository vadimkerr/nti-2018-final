from json import dump, load
import os

# install solc by `pip install py-solc`
from solc import compile_files

def writeDataBase(_data, _file):
    with open(_file, 'w') as out:
        dump(_data, out)

def createNewAccount(_w3, _password, _file):
    if os.path.exists(_file):
        os.remove(_file)
    acc = _w3.personal.newAccount(_password)
    data = {"account": acc, "password": _password}
    writeDataBase(data, _file)
    return data['account']

def unlockAccount(_w3, _actor, _pwd):
    _w3.personal.unlockAccount(_actor, _pwd, 60)

def openDataBase(_file):
    if os.path.exists(_file):
        with open(_file) as file:
            return load(file)
    else:
        return None

def getAccountFromDB(_file):
    data = openDataBase(_file)
    if data is not None:
        return data["account"]
    else:
        return None

# TODO: ask an oracle for gas price
def getActualGasPrice(_w3):
    return _w3.toWei(1, 'gwei')

def compileContracts(_files):
    t = type(_files)
    if t == str:
        contracts = compile_files([_files])
    if t == list:
        contracts = compile_files(_files)
    return contracts

def initializeContractFactory(_w3, _compiledContracts, _key, _address=None):
    if _address == None:
        contract = _w3.eth.contract(
            abi=_compiledContracts[_key]['abi'],
            bytecode=_compiledContracts[_key]['bin']
        )
    else:
        contract = _w3.eth.contract(
            abi=_compiledContracts[_key]['abi'],
            address=_address
        )
    return contract
