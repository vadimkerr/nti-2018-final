from web3 import Web3
from web3.middleware import geth_poa_middleware

import time
import sys
from shutil import move
from decimal import Decimal

# install solc by `pip install py-solc`
from solc import compile_files

from json import load, dump, JSONDecodeError

from utils import publishResultTotal, countResult, checkOutput, printError, \
    setWeb3ProviderShellVariable, getIPCfilePath
from utils import runCmd as runcommand
import os

from random import randint, choice

srcDir = '../src/'
SetupExe = 'setup.py'
VendorExe = 'vendor.py'
ScenterExe = 'scenter.py'
CarExe = 'car.py'
firmwareDir = './firmware'

# Since the solution is run in ./tests directory so CWD for the solution
# will be ./tests directory that's why json files needs to be located in
# this directory as well
databaseFile = 'database.json'
accountsFile = 'account.json'
scenterFile = 'scenter.json'
carFile = 'car.json'

with open('test_accounts.json', 'r') as file:
    actors = load(file)

privKeys = {
    '0x2fe6272cfBcd120c5d0Ce59D22162b8AC6fe032e': '41358ef24fe86a58d67810e1b3eeeba47473b98e75dcaf9a6c295ff445d6d668',
    "0x74337eee6F1BE7F8d1E0BE46D177a42cf12Ee51e": 'c96128075e63206192ed8f70484bab090e08feb8ea1caf2e9665d989ab78a3f4',
    "0x1AE0eC2abb68764F51e250D930dA0FfaAb58f2B7": '56e02f6e0d151d8a9174557d8b9bf5cd347ef1c3891bd4fedbac252d5aa38b90',
    "0xd837adae7b3987461f412c41528EF709bbdad8a8": '1dc435ebc0c90b5826f52d6e9d7d7c146127d893c858e16f564c005b614e658c',
    "0x2c5AD1f8700280ee73261910D1a16dc62c1a7628": '61423bbb54c6b8aee380d24954f3c22941020890f67d3305d0957b180f0dc834'}

setWeb3ProviderShellVariable(getIPCfilePath())

w3 = Web3()

# configure provider to work with PoA chains
w3.middleware_stack.inject(geth_poa_middleware, layer=0)


def setAcc(_actor, _file=accountsFile):
    with open(_file, 'w') as file:
        dump(_actor, file)


def openDataBase(dataFile=databaseFile):
    try:
        with open(dataFile) as _file:
            database = load(_file)
    except FileNotFoundError:
        database = {}
    except JSONDecodeError:
        database = {}
    return database


def writeDataBase(_db, dataFile=databaseFile):
    with open(dataFile, 'w') as file:
        dump(_db, file)


def backupSolutionArtefacts():
    account = os.path.basename(accountsFile)
    db = os.path.basename(databaseFile)
    cwd = os.getcwd()
    if os.path.exists(accountsFile):
        move(accountsFile, cwd + '/' + account)
    if os.path.exists(databaseFile):
        move(databaseFile, cwd + '/' + db)


def restoreSolutionArtefacts():
    account = os.path.basename(accountsFile)
    db = os.path.basename(databaseFile)
    cwd = os.getcwd()
    if os.path.exists(cwd + '/' + account):
        move(cwd + '/' + account, accountsFile)
    if os.path.exists(cwd + '/' + db):
        move(cwd + '/' + db, databaseFile)


def runCmdWithActor(_cmd, _actor, _nobanner=False, _miner=True):
    if _miner:
        w3.miner.start(1)
    setAcc(_actor)
    if _nobanner:
        executed_fmt = '{}'
    else:
        executed_fmt = 'EXECUTED:\n{}'
    print(executed_fmt.format(" ".join(_cmd)))
    ret = runcommand(_cmd)
    if _miner:
        w3.miner.stop()
    return ret


def runCmd(_cmd, _nobanner=False, _miner=False):
    if _miner:
        w3.miner.start(1)
    if _nobanner:
        executed_fmt = '{}'
    else:
        executed_fmt = 'EXECUTED:\n{}'
    print(executed_fmt.format(" ".join(_cmd)))
    ret = runcommand(_cmd)
    if _miner:
        w3.miner.stop()
    return ret


def acc(_actor):
    return _actor['account']


mgmtContract = {}
tokenContract = {}


def compileContracts(_files):
    t = type(_files)
    if t == str:
        contracts = compile_files([_files])
    if t == list:
        contracts = compile_files(_files)
    return contracts


contractFileMgmt = './abi/ManagementContractInterface.sol'
mgmtContractName = 'ManagementContractInterface'
mgmtContractABI = compileContracts(contractFileMgmt)[f'{contractFileMgmt}:{mgmtContractName}']['abi']

contractFileBat = './abi/BatteryManagementInterface.sol'
BatContractName = 'BatteryManagementInterface'
batteryMgmtABI = compileContracts(contractFileBat)[f'{contractFileBat}:{BatContractName}']['abi']


def ManagementContract(_w3, _address):
    return _w3.eth.contract(abi=mgmtContractABI, address=_address)


def BatteryContract(_w3, _address):
    return _w3.eth.contract(abi=batteryMgmtABI, address=_address)


### REFACTORED ########################################################################
def testSetupCreateAccount():
    prev_acc_list = w3.eth.accounts

    cmd = [SetupExe, "--new", "'New_password'"]
    ret = runCmd(cmd)

    retval = False

    if not ret[0]:
        print("The command executed too long")
        return retval

    new_acc_list = w3.eth.accounts

    diff = set(prev_acc_list) ^ set(new_acc_list)
    if len(diff) == 0:
        printError("New account not found on the node", ret[1])
    else:
        account = list(diff)[0]
        retval = checkOutput(ret[1], [account])

    return retval


### REFACTORED ########################################################################
def testSetupCreateManagementContract(_actor, _fee):
    global mgmtContract, currentBatFee, currentRegFee
    currentBatFee = _fee
    currentRegFee = 1000 * currentBatFee

    _cmd = [SetupExe, '--setup', str(currentBatFee)]
    _ret = runCmdWithActor(_cmd, _actor)

    retval = False

    if not _ret[0]:
        print("The command executed too long")
        return retval

    db = openDataBase()
    if not ('mgmtContract' in db):
        printError('Database was not found or it is in incorrect format', _ret[1])
    else:
        mgmtContractAddress = db['mgmtContract']
        mgmtContract = ManagementContract(w3, mgmtContractAddress)

        try:
            batContractAddress = mgmtContract.functions.batteryManagement().call()
        except ValueError as error:
            printError("Cannot call batteryManagement()", [error])
            return retval

        batContract = BatteryContract(w3, batContractAddress)

        try:
            erc20ContractAddress = batContract.functions.erc20().call()
        except ValueError as error:
            printError("Cannot call erc20()", [error])
            return retval

        try:
            walletContractAddress = mgmtContract.functions.walletContract().call()
        except ValueError as error:
            printError("Cannot call erc20()", [error])
            return retval

        forma = 'Management contract: {}\nWallet contract: {}\nCurrency contract: {}'
        forma = forma.format(mgmtContractAddress, walletContractAddress, erc20ContractAddress).split('\n')

        retval = checkOutput(_ret[1], forma)
    return retval


### REFACTORED ########################################################################
def testVendorNewAccount():
    prev_acc_list = w3.eth.accounts

    cmd = [VendorExe, "--new", "'New_password'"]
    ret = runCmd(cmd)

    retval = False

    if not ret[0]:
        print("The command executed too long")
        return retval

    new_acc_list = w3.eth.accounts

    diff = set(prev_acc_list) ^ set(new_acc_list)
    if len(diff) == 0:
        printError("New account not found on the node", ret[1])
    else:
        account = list(diff)[0]
        retval = checkOutput(ret[1], [account])

    return retval


### REFACTORED ########################################################################
def VendorRegisterNewVendorSuccess(_actor, _name, _value):
    walletContractAddress = mgmtContract.functions.walletContract().call()
    prev_balance = w3.eth.getBalance(walletContractAddress)

    cmd = [VendorExe, '--reg', _name, str(_value)]
    _ret = runCmdWithActor(cmd, _actor)

    retval = False

    if not _ret[0]:
        print("The command executed too long")
        return retval

    cur_balance = w3.eth.getBalance(walletContractAddress)
    wei_value = w3.toWei(_value, 'ether')

    if not (cur_balance - prev_balance == wei_value):
        printError("Wallet balance was not changed", _ret[1])
        return retval

    try:
        deposit = mgmtContract.functions.vendorDeposit(_actor['account']).call()
    except ValueError as error:
        printError("Cannot call vendorDeposit()", [error])
        return retval

    if deposit != wei_value:
        printError("Deposit differs", _ret[1])
        return retval

    try:
        vendId = mgmtContract.functions.vendorId(_actor['account']).call()
    except ValueError as error:
        printError("Cannot call vendorDeposit()", [error])
        return retval

    forma = 'Success.\nVendor ID: {}'.format(str(w3.toHex(vendId))[2:])
    forma = forma.split('\n')
    retval = checkOutput(_ret[1], forma)

    return retval


### REFACTORED ########################################################################
def VendorRegOneBattery(_actor, _value=0):
    global exist_batId, batContract
    walletContractAddress = mgmtContract.functions.walletContract().call()
    prev_balance = w3.eth.getBalance(walletContractAddress)
    batId = None
    if _value == 0:
        cmd = [VendorExe, '--bat', '1']
    else:
        cmd = [VendorExe, '--bat', '1', str(_value)]
    _ret = runCmdWithActor(cmd, _actor)

    retval = False

    if not _ret[0]:
        print("The command executed too long or there is nothing on output")
        return retval

    cur_balance = w3.eth.getBalance(walletContractAddress)
    wei_value = w3.toWei(_value, 'ether')

    if not (prev_balance + wei_value == cur_balance):
        printError("Wallet balance was not changed", _ret[1])
        return retval

    if (len(_ret[1]) == 0):
        printError("No output", _ret[1])
    else:
        batId = _ret[1][0].strip()[-40:]
        try:
            n = w3.toInt(hexstr=batId)
        except ValueError:
            printError("No battery Id in the output", _ret[1])
        else:
            h = w3.toHex(n)[2:]
            sh = delHexPrefix(str(h).lower())
            sh = '0'*(40-len(sh))+sh
            retval = (sh == delHexPrefix(str(batId).lower()))

            if not (retval):
                printError("Have not hex in output", _ret[1])

    if not retval:
        return retval

    batContractAddress = mgmtContract.functions.batteryManagement().call()
    batContract = BatteryContract(w3, batContractAddress)

    retval = False
    batId = w3.toBytes(hexstr=batId)
    try:
        vendAddr = batContract.functions.vendorOf(batId).call()
    except ValueError as error:
        printError("Cannot call vendorOf()", [error])
    else:
        try:
            ownerAddr = batContract.functions.ownerOf(batId).call()
        except ValueError as error:
            printError("Cannot call ownerOf()", [error])
        else:
            if (vendAddr == '0x' + '0' * 40) or (vendAddr != ownerAddr):
                printError("Incorrect info in Battery management contract", _ret[1])
            else:
                exist_batId = batId
                retval = True

    return retval

def VendorRegOneBatteryWithChangedFee(_setfeeactor, _actor, _newfee):
    _cmd = [SetupExe, '--setfee', str(_newfee)]
    _ret = runCmdWithActor(_cmd, _setfeeactor)

    retval = False

    if not _ret[0]:
        print("The command executed too long or there is nothing on output")
        return retval
 
    try:
        prev_deposit = mgmtContract.functions.vendorDeposit(_actor['account']).call()
    except ValueError as error:
        printError("Cannot call vendorDeposit()", [error])
        return retval

    cmd = [VendorExe, '--bat', '1']
    _ret = runCmdWithActor(cmd, _actor, True)

    retval = False

    if not _ret[0]:
        print("The command executed too long or there is nothing on output")
        return retval

    try:
        cur_deposit = mgmtContract.functions.vendorDeposit(_actor['account']).call()
    except ValueError as error:
        printError("Cannot call vendorDeposit()", [error])
        return retval

    retval = prev_deposit-cur_deposit == w3.toWei(currentBatFee, 'ether')
    if not retval:
        printError("Deposit differs unexpectedly", _ret[1])
        return retval

    return retval

### REFACTORED ########################################################################
def ScenterNewAccount():
    prev_acc_list = w3.eth.accounts

    cmd = [ScenterExe, "--new", "'New_password'"]
    _ret = runCmd(cmd)

    retval = False

    if not _ret[0]:
        print("The command executed too long or there is nothing on output")
        return retval

    new_acc_list = w3.eth.accounts

    diff = set(prev_acc_list) ^ set(new_acc_list)
    if len(diff) == 0:
        printError("New account not found on the node", _ret[1])
    else:
        account = list(diff)[0]
        retval = checkOutput(_ret[1], [account])

    return retval


### REFACTORED ########################################################################
def ScenterRegTwoOptions(_actor, _failed=False):
    setAcc(_actor, scenterFile)

    cmd = [ScenterExe, '--reg']
    _ret = runCmd(cmd, _miner=True)

    retval = False

    if not _ret[0]:
        print("The command executed too long or there is nothing on output")
        return retval

    try:
        flag = mgmtContract.functions.serviceCenters(_actor["account"]).call()
    except ValueError as error:
        printError("Cannot call serviceCenters()", [error])
        return retval

    if not flag:
        printError("Got 'False' from contract", _ret[1])
        return retval

    if not _failed:
        forma = ['Registered successfully']
    else:
        forma = ['Already registered']
    return checkOutput(_ret[1], forma)


def privtopub(key):
    return w3.eth.account.privateKeyToAccount(key).address


### REFACTORED ########################################################################
def CarNewAccount():
    cmd = [CarExe, "--new"]
    _ret = runCmd(cmd)

    retval = False

    if not _ret[0]:
        print("The command executed too long or there is nothing on output")
        return retval

    data = openDataBase(carFile)
    if 'key' not in data:
        printError("Incorrect database", _ret[1])
        return retval

    return checkOutput(_ret[1], [privtopub(data['key'])])


### REFACTORED ########################################################################
def CarGetAccount(_actor):
    data = {'key': privKeys[_actor['account']]}
    writeDataBase(data, carFile)

    cmd = [CarExe, "--account"]
    _ret = runCmd(cmd)

    retval = False

    if not _ret[0]:
        print("The command executed too long or there is nothing on output")
        return retval

    return checkOutput(_ret[1], [_actor['account']])


### REFACTORED ########################################################################
def CarRegTwoOptions(_actor, _failed=False):
    data = {'key': privKeys[_actor['account']]}
    writeDataBase(data, carFile)

    cmd = [CarExe, '--reg']
    _ret = runCmd(cmd, _miner=True)

    retval = False

    if not _ret[0]:
        print("The command executed too long or there is nothing on output")
        return retval

    try:
        flag = mgmtContract.functions.cars(_actor["account"]).call()
    except ValueError as error:
        printError("Cannot call cars()", [error])
        return retval

    if not flag:
        printError("Got 'False' from contract", _ret[1])
        return retval

    if not _failed:
        forma = ['Registered successfully']
    else:
        forma = ['Already registered']
    return checkOutput(_ret[1], forma)

def SetupSetFeeTwoOptions(_actor, _fee, _failed=False):
    global currentBatFee, currentRegFee

    _cmd = [SetupExe, '--setfee', str(_fee)]
    _ret = runCmdWithActor(_cmd, _actor)

    retval = False

    if not _ret[0]:
        print("The command executed too long")
        return retval

    if (len(_ret[1]) == 0):
        printError("No output")
        return retval
    else:
        newBatFee = w3.toWei(_fee, 'ether')

        try:
            currentBatFeeWei = mgmtContract.functions.batteryFee().call()
        except ValueError as error:
            printError("Cannot call batteryFee()", [error])
            return retval

        currentBatFee = w3.fromWei(currentBatFeeWei, 'ether')
        currentRegFee = Decimal.normalize(1000 * currentBatFee)

        if newBatFee != currentBatFeeWei:
            printError("Fee was not set", _ret[1])
            return retval

        if not _failed:
            forma = ['Updated successfully']
        else:
            forma = ['No permissions to change the service fee']

        return checkOutput(_ret[1], forma)

def testVendorGetRegFee():
    cmd = [VendorExe, '--regfee']
    _ret = runCmd(cmd)

    retval = False

    if not _ret[0]:
        print("The command executed too long or there is nothing on output")
        return retval
    return checkOutput(_ret[1], [f"Vendor registration fee: {currentRegFee}"])

def VendorRegisterLowPaymentFail(_actor, _name, _value):
    walletContractAddress = mgmtContract.functions.walletContract().call()
    prev_balance = w3.eth.getBalance(walletContractAddress)

    cmd = [VendorExe, '--reg', _name, str(_value)]
    _ret = runCmdWithActor(cmd, _actor)

    retval = False

    if not _ret[0]:
        print("The command executed too long")
        return retval

    cur_balance = w3.eth.getBalance(walletContractAddress)

    if not (cur_balance - prev_balance == 0):
        printError("Wallet balance was changed", _ret[1])
        return retval

    try:
        deposit = mgmtContract.functions.vendorDeposit(_actor['account']).call()
    except ValueError as error:
        printError("Cannot call vendorDeposit()", [error])
        return retval

    if deposit != 0:
        print(deposit)
        printError("Vendor was registered. Deposit is not equal to zero", _ret[1])
        return retval

    retval = checkOutput(_ret[1], ['Failed. Payment is low.'])

    return retval

def VendorRegisterInsufficientFundsFail(_name, _value):
    walletContractAddress = mgmtContract.functions.walletContract().call()
    prev_balance = w3.eth.getBalance(walletContractAddress)

    password = "testPassword"
    actor = {"account": w3.personal.newAccount(password), "password": password}

    cmd = [VendorExe, '--reg', _name, str(_value)]
    _ret = runCmdWithActor(cmd, actor)

    retval = False

    if not _ret[0]:
        print("The command executed too long")
        return retval

    cur_balance = w3.eth.getBalance(walletContractAddress)

    if not (cur_balance - prev_balance == 0):
        printError("Wallet balance was changed", _ret[1])
        return retval

    try:
        deposit = mgmtContract.functions.vendorDeposit(actor['account']).call()
    except ValueError as error:
        printError("Cannot call vendorDeposit()", [error])
        return retval

    if deposit != 0:
        print(deposit)
        printError("Vendor was registered. Deposit is not equal to zero", _ret[1])
        return retval

    retval = checkOutput(_ret[1], ['Failed. No enough funds to deposit.'])

    return retval

def VendorRegisterNotUniqueNameFail(_actor, _name, _value):
    walletContractAddress = mgmtContract.functions.walletContract().call()
    prev_balance = w3.eth.getBalance(walletContractAddress)

    cmd = [VendorExe, '--reg', _name, str(_value)]
    _ret = runCmdWithActor(cmd, _actor)

    retval = False

    if not _ret[0]:
        print("The command executed too long")
        return retval

    cur_balance = w3.eth.getBalance(walletContractAddress)

    if not (cur_balance - prev_balance == 0):
        printError("Wallet balance was changed", _ret[1])
        return retval

    try:
        deposit = mgmtContract.functions.vendorDeposit(_actor['account']).call()
    except ValueError as error:
        printError("Cannot call vendorDeposit()", [error])
        return retval

    if deposit != 0:
        print(deposit)
        printError("Vendor was registered. Deposit is not equal to zero", _ret[1])
        return retval

    retval = checkOutput(_ret[1], ['Failed. The vendor name is not unique.'])

    return retval

def VendorRegisterNotUniqueAddressFail(_actor, _name, _value):
    walletContractAddress = mgmtContract.functions.walletContract().call()
    prev_balance = w3.eth.getBalance(walletContractAddress)

    cmd = [VendorExe, '--reg', _name, str(_value)]
    _ret = runCmdWithActor(cmd, _actor)

    retval = False

    if not _ret[0]:
        print("The command executed too long")
        return retval

    cur_balance = w3.eth.getBalance(walletContractAddress)

    if not (cur_balance - prev_balance == 0):
        printError("Wallet balance was changed", _ret[1])
        return retval

    try:
        deposit = mgmtContract.functions.vendorDeposit(_actor['account']).call()
    except ValueError as error:
        printError("Cannot call vendorDeposit()", [error])
        return retval

    retval = checkOutput(_ret[1], ['Failed. The vendor address already used.'])

    return retval

def VendorGetBatteryFee(_actor):
    cmd = [VendorExe, '--batfee']
    _ret = runCmdWithActor(cmd, _actor)

    retval = False

    if not _ret[0]:
        print("The command executed too long or there is nothing on output")
        return retval
    return checkOutput(_ret[1], [f"Production fee per one battery: {currentBatFee}"])

def VendorGetBatteryFeeAfterChange(_setfeeactor, _actor, _newfee):
    _cmd = [SetupExe, '--setfee', str(_newfee)]
    _ret = runCmdWithActor(_cmd, _setfeeactor)

    retval = False

    if not _ret[0]:
        print("The command executed too long or there is nothing on output")
        return retval
  
    _cmd = [VendorExe, '--batfee']
    _ret = runCmdWithActor(_cmd, _actor, True)

    if not _ret[0]:
        print("The command executed too long or there is nothing on output")
        return retval

    return checkOutput(_ret[1], [f"Production fee per one battery: {currentBatFee}"])

def delHexPrefix(_s: str):
    if _s[:2] == '0x':
        _s = _s[2:]
    return _s


def VendorOwnerOneBattery(_actor, _failed=False):
    global exist_batId, batContract
    _newOwner = _actor['account']
    _batId = exist_batId
    cmd = [VendorExe, '--owner', delHexPrefix(w3.toHex(_batId)), _newOwner]
    _ret = runCmdWithActor(cmd, ownerVendor)

    retval = False

    if not _ret[0]:
        print(_ret[1])
        print("The command executed too long or there is nothing on output")
        return retval

    try:
        vendAddr = batContract.functions.vendorOf(_batId).call()
    except ValueError as error:
        printError("Cannot call vendorOf()", [error])
        return retval

    try:
        ownerAddr = batContract.functions.ownerOf(_batId).call()
    except ValueError as error:
        printError("Cannot call ownerOf()", [error])
        return retval
    forma = []
    if not _failed:
        forma = ['Success']
        if (vendAddr == '0x' + '0' * 40) or (_newOwner != ownerAddr):
            printError("Incorrect info in Battery management contract", _ret[1])
            return retval
    else:
        forma = ['Failed. Not allowed to change ownership.']
        if (vendAddr == '0x' + '0' * 40) or (_newOwner == ownerAddr):
            printError("Incorrect info in Battery management contract", _ret[1])
            return retval

    return checkOutput(_ret[1], forma)

def VendorDeposit(_actor):
    cmd = [VendorExe, '--deposit']
    _ret = runCmdWithActor(cmd, _actor)

    retval = False

    if not _ret[0]:
        print("The command executed too long or there is nothing on output")
        return retval

    try:
        cur_deposit = mgmtContract.functions.vendorDeposit(_actor['account']).call()
    except ValueError as error:
        printError("Cannot call vendorDeposit()", [error])
        return retval

    forma = ['Deposit: {}'.format(w3.fromWei(cur_deposit, 'ether'))]
    return checkOutput(_ret[1], forma)

def VendorDepositWrongAccount(_actor):
    cmd = [VendorExe, '--deposit']
    _ret = runCmdWithActor(cmd, _actor)

    retval = False

    if not _ret[0]:
        print("The command executed too long or there is nothing on output")
        return retval

    forma = ['Vendor account is not registered.']
    return checkOutput(_ret[1], forma)

def VendorRegFewBatteries(_actor, _num, _value=0):
    walletContractAddress = mgmtContract.functions.walletContract().call()
    prev_balance = w3.eth.getBalance(walletContractAddress)
    batId = None
    if _value == 0:
        cmd = [VendorExe, '--bat', str(_num)]
    else:
        cmd = [VendorExe, '--bat', str(_num), str(_value)]
    _ret = runCmdWithActor(cmd, _actor)

    retval = False

    if not _ret[0]:
        print("The command executed too long or there is nothing on output")
        return retval

    cur_balance = w3.eth.getBalance(walletContractAddress)
    wei_value = w3.toWei(_value, 'ether')

    if not (prev_balance + wei_value == cur_balance):
        printError("Wallet balance was not changed", _ret[1])
        return retval

    if (len(_ret[1]) != _num):
        printError("Not enough new batteries", _ret[1])
    else:
        retval = True

    return retval

def CreateFirmware(_actor, _num):

    if os.path.exists(firmwareDir):
        for the_file in os.listdir(firmwareDir):
            file_path = os.path.join(firmwareDir, the_file)
            try:
                if os.path.isfile(file_path):
                   os.unlink(file_path)
            except Exception as e:
                printError('Cannot clean a firmware directory', [e])
                return False

    cmd = [VendorExe, '--bat', str(_num)]
    _ret = runCmdWithActor(cmd, _actor)

    retval = False

    if not _ret[0]:
        print("The command executed too long or there is nothing on output")
        return retval

    num_files = 0
    files = []
    if os.path.exists(firmwareDir):
        for the_file in os.listdir(firmwareDir):
            file_path = os.path.join(firmwareDir, the_file)
            files.append(file_path)
            if os.path.isfile(file_path):
                num_files = num_files + 1
    
    retval = num_files == _num
    if not retval:
        printError('Number of generated firmwares is not correct', files)

    return retval

def FirmwareCheckCharges():

    files = []
    if os.path.exists(firmwareDir):
        for the_file in os.listdir(firmwareDir):
            file_path = os.path.join(firmwareDir, the_file)
            if os.path.isfile(file_path):
                files.append(the_file)

    retval = False
    
    curdir = os.getcwd()
    os.chdir(firmwareDir)

    fw = choice(files)

    cmd = [fw, '--charge']
    _ret = runCmd(cmd)
    if _ret[0]:
        printError("Output is not expected, or something went wrong", _ret[1])
        return retval
    _ret = runCmd(cmd, True)
    if _ret[0]:
        printError("Output is not expected, or something went wrong", _ret[1])
        return retval
    _ret = runCmd(cmd, True)
    if _ret[0]:
        printError("Output is not expected, or something went wrong", _ret[1])
        return retval

    cmd = [fw, '--get']
    _ret = runCmd(cmd, True)

    os.chdir(curdir)

    if not _ret[0]:
        print("The command executed too long or there is nothing on output")
        return retval

    if len(_ret[1]) != 5:
        printError('Firwmare output is not correct', _ret[1])
    else:
        retval = int(_ret[1][0]) == 3
        if not retval:
            printError('Firwmare output is not correct', _ret[1])
    
    return retval


currentBatFee = 0
RegVendor = {}
RegFee = {}
BatFee = {}
exist_batId = None
testsdir = os.getcwd()
os.chdir(srcDir)

if os.path.exists(accountsFile):
    os.remove(accountsFile)
if os.path.exists(databaseFile):
    os.remove(databaseFile)
if os.path.exists(scenterFile):
    os.remove(scenterFile)
if os.path.exists(carFile):
    os.remove(carFile)

ownerMgmtContract = actors['account1']
ownerVendor = actors['account2']
Scenter = actors['account3']
car = actors['account4']
user1 = actors['account5']

ac00101_setup_new_account = False
ac00201_setup_deploy_contracts = False
ac00301_setup_setfee = False
ac00302_setup_setfee_fail = False
ac00501_vendor_new_account = False
ac00601_vendor_regfee_value = False
ac00701_vendor_new_vendor = False
ac00702_vendor_new_vendor_fail_low_payment = False
ac00703_vendor_new_vendor_fail_insufficient_funds = False
ac00801_vendor_new_vendor_fail_not_unique_name = False
ac00802_vendor_new_vendor_fail_not_unique_address = False
ac00901_vendor_get_battery_fee = False
ac00901_vendor_get_battery_fee_after_change = False
ac01001_vendor_one_battery_no_value = False
ac01003_vendor_one_battery_and_value = False
ac01101_vendor_one_battery_batfee_changed = False
ac01201_vendor_get_deposit = False
ac01202_vendor_get_deposit_wrong_account = False
ac01301_vendor_few_batteries_no_value = False
ac01303_vendor_few_batteries_and_value = False
ac01401_vendor_more_than_one_battery_no_value = False
ac01501_vendor_one_battery_no_value = False
ac01502_vendor_one_battery_no_value = False
ac01503_vendor_one_battery_no_value = False
ac01701_firmware_created = False
ac01801_firmware_charge = False
ac01901_firmware_get = False
ac02001_scenter_new_account = False
ac02101_scenter_reg_account = False
ac02102_scenter_reg_account_fail = False
ac02201_car_new_account = False
ac02301_car_get_account = False
ac02401_car_reg_account = False
ac02402_car_reg_account_fail = False

ac = "AC-001-01"
print(f'{ac}: check setup.py to create new account')
ac00101_setup_new_account = testSetupCreateAccount()
countResult(ac00101_setup_new_account, ac)

ac = "AC-002-01"
print(f'{ac}: check setup.py to deploy contracts')
ac00201_setup_deploy_contracts = testSetupCreateManagementContract(ownerMgmtContract, 0.00017)
countResult(ac00201_setup_deploy_contracts, ac)

ac="AC-003-01"
print(f'{ac}: check setup.py to set fee')
if ac00201_setup_deploy_contracts:
    ac00301_setup_setfee = SetupSetFeeTwoOptions(ownerMgmtContract, 0.0005, False)
countResult(ac00301_setup_setfee, ac)

ac="AC-003-02"
print(f'{ac}: check setup.py to set fee by account with no permission')
if ac00301_setup_setfee:
    ac00302_setup_setfee_fail = SetupSetFeeTwoOptions(user1, 0.0005, True)
countResult(ac00302_setup_setfee_fail, ac)

# AC-004-01 - third day
# AC-004-02 - third day

ac = "AC-005-01"
print(f'{ac}: check vendor.py to create new account')
ac00501_vendor_new_account = testVendorNewAccount()
countResult(ac00501_vendor_new_account, ac)

ac="AC-006-01"
print(f'{ac}: check vendor.py to get registation fee')
if ac00201_setup_deploy_contracts and ac00301_setup_setfee:
    ac00601_vendor_regfee_value = testVendorGetRegFee()
countResult(ac00601_vendor_regfee_value, ac)

ac = "AC-007-01"
print(f'{ac}: check vendor.py to register new vendor')
if ac00201_setup_deploy_contracts:
    ac00701_vendor_new_vendor = VendorRegisterNewVendorSuccess(ownerVendor, 'TestName', currentRegFee)
countResult(ac00701_vendor_new_vendor, ac)

ac="AC-007-02"
print(f'{ac}: check vendor.py to register new vendor with low deposit')
if ac00701_vendor_new_vendor:
    ac00702_vendor_new_vendor_fail_low_payment = VendorRegisterLowPaymentFail(user1, 'TestName2', currentRegFee-currentBatFee)
countResult(ac00702_vendor_new_vendor_fail_low_payment, ac)

ac="AC-007-03"
print(f'{ac}: check vendor.py to register new vendor without enough funds')
if ac00701_vendor_new_vendor:
    ac00703_vendor_new_vendor_fail_insufficient_funds = VendorRegisterInsufficientFundsFail('TestName2', currentRegFee)
countResult(ac00703_vendor_new_vendor_fail_insufficient_funds, ac)

ac="AC-008-01"
print(f'{ac}: check vendor.py to register new vendor with not unique name')
if ac00701_vendor_new_vendor:
    ac00801_vendor_new_vendor_fail_not_unique_name = VendorRegisterNotUniqueNameFail(user1, 'TestName', currentRegFee)
countResult(ac00801_vendor_new_vendor_fail_not_unique_name , ac)

ac="AC-008-02"
print(f'{ac}: check vendor.py to register new vendor with not unique address')
if ac00701_vendor_new_vendor:
    ac00802_vendor_new_vendor_fail_not_unique_address = VendorRegisterNotUniqueAddressFail(ownerVendor, 'TestName2', currentRegFee)
countResult(ac00802_vendor_new_vendor_fail_not_unique_address, ac)

ac="AC-009-01"
print(f'{ac}: check vendor.py to get battery fee')
if ac00201_setup_deploy_contracts and ac00301_setup_setfee:
    ac00901_vendor_get_battery_fee = VendorGetBatteryFee(ownerVendor)
countResult(ac00901_vendor_get_battery_fee, ac)

ac="AC-009-02"
print(f'{ac}: check vendor.py to get battery fee after it was changed')
if ac00901_vendor_get_battery_fee:
    ac00901_vendor_get_battery_fee_after_change = VendorGetBatteryFeeAfterChange(ownerMgmtContract, ownerVendor, 0.0001)
countResult(ac00901_vendor_get_battery_fee_after_change, ac)

ac = "AC-010-01"
print(f'{ac}: check vendor.py to register one battery')
if ac00701_vendor_new_vendor:
    ac01001_vendor_one_battery_no_value = VendorRegOneBattery(ownerVendor)
countResult(ac01001_vendor_one_battery_no_value, ac)

# AC-010-02 skipped

ac = "AC-010-03"
print(f'{ac}: check vendor.py to register one battery with extra deposit')
if ac00701_vendor_new_vendor:
    ac01003_vendor_one_battery_and_value = VendorRegOneBattery(ownerVendor, currentBatFee)
countResult(ac01003_vendor_one_battery_and_value, ac)

ac = "AC-011-01"
print(f'{ac}: check vendor.py to register one battery even if the battery fee was changed')
if ac01001_vendor_one_battery_no_value:
    ac01101_vendor_one_battery_batfee_changed = VendorRegOneBatteryWithChangedFee(ownerMgmtContract, ownerVendor, 0.0001)
countResult(ac01101_vendor_one_battery_batfee_changed, ac)

ac = "AC-012-01"
print(f'{ac}: check vendor.py to get depost')
if ac00701_vendor_new_vendor:
    ac01201_vendor_get_deposit = VendorDeposit(ownerVendor)
countResult(ac01201_vendor_get_deposit, ac)

ac = "AC-012-02"
print(f'{ac}: check vendor.py to get depost from incorrect account')
if ac01201_vendor_get_deposit:
    ac01202_vendor_get_deposit_wrong_account = VendorDepositWrongAccount(user1)
countResult(ac01202_vendor_get_deposit_wrong_account, ac)

ac = "AC-013-01"
print(f'{ac}: check vendor.py to register few batteries')
if ac01001_vendor_one_battery_no_value:
    ac01301_vendor_few_batteries_no_value = VendorRegFewBatteries(ownerVendor, 2)
countResult(ac01301_vendor_few_batteries_no_value, ac)

# AC-013-02 - skip

ac = "AC-013-03"
print(f'{ac}: check vendor.py to register few battery with extra deposit')
if ac01001_vendor_one_battery_no_value:
    ac01303_vendor_few_batteries_and_value = VendorRegFewBatteries(ownerVendor, 5, currentBatFee*5)
countResult(ac01303_vendor_few_batteries_and_value, ac)


# third day 
# ac = "AC-014-01"
# print(f'{ac}: check vendor.py to register more than one battery ')
# if ac00701_vendor_new_vendor:
#    ac01401_vendor_more_than_one_battery_no_value = VendorOwnerOneBattery(ownerVendor)
# countResult(ac01401_vendor_more_than_one_battery_no_value, ac)

ac = "AC-020-01"
print(f'{ac}: check scenter.py to create new account')
ac02001_scenter_new_account = ScenterNewAccount()
countResult(ac02001_scenter_new_account, ac)

ac = "AC-021-01"
print(f'{ac}: check scenter.py to register account')
if ac00201_setup_deploy_contracts and ac02001_scenter_new_account:
    ac02101_scenter_reg_account = ScenterRegTwoOptions(Scenter)
countResult(ac02101_scenter_reg_account, ac)

ac = "AC-015-01"
print(f'{ac}: check vendor.py to change of one battery owner')
if ac01001_vendor_one_battery_no_value and ac01003_vendor_one_battery_and_value:
    ac01501_vendor_one_battery_no_value = VendorOwnerOneBattery(Scenter)
countResult(ac01501_vendor_one_battery_no_value, ac)

ac = "AC-015-02"
print(f'{ac}: check vendor.py to change of one battery owner from not owner')
if ac01501_vendor_one_battery_no_value:
    ac01502_vendor_one_battery_no_value = VendorOwnerOneBattery(ownerVendor, True)
countResult(ac01502_vendor_one_battery_no_value, ac)

ac = "AC-015-03"
print(f'{ac}: check vendor.py to change of owner one battery to unregistered user')
if ac01501_vendor_one_battery_no_value:
    ac01503_vendor_one_battery_no_value = VendorOwnerOneBattery(ownerVendor, True)
countResult(ac01503_vendor_one_battery_no_value, ac)

# AC-016-01 - third day

ac = "AC-017-01"
print(f'{ac}: check vendor.py to create batteries firmware')
if ac01301_vendor_few_batteries_no_value:
    ac01701_firmware_created = CreateFirmware(ownerVendor, randint(2, 7))
countResult(ac01701_firmware_created, ac)

ac = "AC-018-01"
print(f'{ac}: check firmware to charge')
if ac01701_firmware_created:
    ac01801_firmware_charge = FirmwareCheckCharges()
countResult(ac01801_firmware_charge, ac)

ac = "AC-019-01"
print(f'{ac}: check firmware to get status')
if ac01701_firmware_created:
    ac01901_firmware_get = ac01801_firmware_charge
countResult(ac01901_firmware_get, ac)

ac = "AC-021-02"
print(f'{ac}: check scenter.py to register the same account second time')
if ac02101_scenter_reg_account:
    ac02102_scenter_reg_account_fail = ScenterRegTwoOptions(Scenter, True)
countResult(ac02102_scenter_reg_account_fail, ac)

ac = "AC-022-01"
print(f'{ac}: check car.py to create new account')
ac02201_car_new_account = CarNewAccount()
countResult(ac02201_car_new_account, ac)

ac = "AC-023-01"
print(f'{ac}: check car.py to provide account address')
ac02301_car_get_account = CarGetAccount(car)
countResult(ac02301_car_get_account, ac)

ac = "AC-024-01"
print(f'{ac}: check car.py to register account')
if ac00201_setup_deploy_contracts and ac02201_car_new_account:
    ac02401_car_reg_account = CarRegTwoOptions(car)
countResult(ac02401_car_reg_account, ac)

ac = "AC-024-02"
print(f'{ac}: check car.py to register the same account second time')
if ac02401_car_reg_account:
    ac02402_car_reg_account_fail = CarRegTwoOptions(car, True)
countResult(ac02402_car_reg_account_fail, ac)

# AC-025-01
# AC-025-02
# AC-025-03 - third day

# AC-026-01
# AC-026-02
# AC-026-03 - third day

os.chdir(testsdir)

publishResultTotal()

sys.exit('Finished')
