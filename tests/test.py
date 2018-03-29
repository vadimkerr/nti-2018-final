from web3 import Web3
from web3.middleware import geth_poa_middleware

import time
import sys
from shutil import move

# install solc by `pip install py-solc`
from solc import compile_files

from json import load, dump, JSONDecodeError

from utils import publishResultTotal, countResult, checkOutput, printError, \
    setWeb3ProviderShellVariable, getIPCfilePath
from utils import runCmd as runcommand
import os

srcDir = '../src/'
SetupExe = 'setup.py'
VendorExe = 'vendor.py'
ScenterExe = 'scenter.py'
CarExe = 'car.py'

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
            printError("Cannot call batteryManagement()", [error], _ret[1])
            return retval
        
        batContract = BatteryContract(w3, batContractAddress)
                                        
        try:
            erc20ContractAddress = batContract.functions.erc20().call()
        except ValueError as error:
            printError("Cannot call erc20()", [error], _ret[1])
            return retval

        try:
            walletContractAddress = mgmtContract.functions.walletContract().call()
        except ValueError as error:
            printError("Cannot call erc20()", [error], _ret[1])
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
    
    if not (cur_balance-prev_balance == wei_value):
        printError("Wallet balance was not changed", _ret[1])
        return retval

    try:
        deposit = mgmtContract.functions.vendorDeposit(_actor['account']).call()
    except ValueError as error:
        printError("Cannot call vendorDeposit()", [error], _ret[1])
        return retval

    if deposit != wei_value:
        printError("Deposit differs", _ret[1])
        return retval

    try:
        vendId = mgmtContract.functions.vendorId(_actor['account']).call()
    except ValueError as error:
        printError("Cannot call vendorDeposit()", [error], _ret[1])
        return retval

    forma = 'Success.\nVendor ID: {}'.format(str(w3.toHex(vendId))[2:])
    forma = forma.split('\n')
    retval = checkOutput(_ret[1], forma)

    return retval

### REFACTORED ########################################################################
def VendorRegOneBattery(_actor, _value=0):
    walletContractAddress = mgmtContract.functions.walletContract().call()
    prev_balance = w3.eth.getBalance(walletContractAddress)

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

    if not (prev_balance+wei_value == cur_balance):
        printError("Wallet balance was not changed", _ret[1])
        return retval
    
    if (len(_ret[1]) == 0):
        printError("No output", _ret[1])
    else:
        bId = _ret[1][0].strip()[-39:]
        try:
            n = w3.toInt(hexstr=bId)
        except ValueError:
            printError("No battery Id in the output", _ret[1])
        else:
            h = w3.toHex(n)[2:]
            retval = (h == bId)
            if not (retval):
                printError("No battery Id in the output", _ret[1])
    return retval

    batId = _ret[1][0].strip()

    batContractAddress = mgmtContract.functions.batteryManagement().call()
    batContract = BatteryContract(w3, batContractAddress)

    try:
        vendAddr = batContract.functions.vendorOf(batId).call()
    except ValueError as error:
        printError("Cannot call vendorOf()", [error], _ret[1])
        return retval

    try:
        ownerAddr = batContract.functions.ownerOf(batId).call()
    except ValueError as error:
        printError("Cannot call ownerOf()", [error], _ret[1])
        return retval

    if (vendAddr == '0x'+'0'*40) or (vendAddr != ownerAddr):
        printError("Incorrect info in Battery management contract", _ret[1])
        return retval

    return True

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
        printError("Cannot call serviceCenters()", [error], _ret[1])
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
        printError("Cannot call cars()", [error], _ret[1])
        return retval

    if not flag:
        printError("Got 'False' from contract", _ret[1])
        return retval

    if not _failed:
        forma = ['Registered successfully']
    else:
        forma = ['Already registered']
    return checkOutput(_ret[1], forma)

currentRegFee = 0
currentBatFee = 0
RegVendor = {}
RegFee = {}
BatFee = {}

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
user1 = actors['account4']
user2 = actors['account5']

ac00101_setup_new_account = False
ac00201_setup_deploy_contracts = False
ac00501_vendor_new_account = False
ac00701_vendor_new_vendor = False
ac01001_vendor_one_battery_no_value = False
ac01003_vendor_one_battery_and_value = False
ac02001_scenter_new_account = False
ac02101_scenter_reg_account = False
ac02102_scenter_reg_account_fail = False
ac02201_car_new_account = False
ac02301_car_get_account = False
ac02401_car_reg_account = False
ac02402_car_reg_account_fail = False

ac="AC-001-01"
print(f'{ac}: check setup.py to create new account')
ac00101_setup_new_account = testSetupCreateAccount()
countResult(ac00101_setup_new_account, ac)

ac="AC-002-01"
print(f'{ac}: check setup.py to deploy contracts')
if ac00101_setup_new_account:
    ac00201_setup_deploy_contracts = testSetupCreateManagementContract(ownerMgmtContract, 0.00017)
countResult(ac00201_setup_deploy_contracts, ac)

ac="AC-005-01"
print(f'{ac}: check vendor.py to create new account')
ac00501_vendor_new_account = testVendorNewAccount()
countResult(ac00501_vendor_new_account, ac)

ac="AC-007-01"
print(f'{ac}: check vendor.py to register new vendor')
if ac00201_setup_deploy_contracts:
    ac00701_vendor_new_vendor = VendorRegisterNewVendorSuccess(ownerVendor, 'TestName', currentRegFee)
countResult(ac00701_vendor_new_vendor, ac)

ac="AC-010-01"
print(f'{ac}: check vendor.py to register one battery')
if ac00701_vendor_new_vendor:
    ac01001_vendor_one_battery_no_value = VendorRegOneBattery(ownerVendor)
countResult(ac01001_vendor_one_battery_no_value, ac)

ac="AC-010-03"
print(f'{ac}: check vendor.py to register one battery with extra deposit')
if ac00701_vendor_new_vendor:
    ac01003_vendor_one_battery_and_value = VendorRegOneBattery(ownerVendor, currentBatFee)
countResult(ac01003_vendor_one_battery_and_value, ac)

ac="AC-020-01"
print(f'{ac}: check scenter.py to create new account')
ac02001_scenter_new_account = ScenterNewAccount()
countResult(ac02001_scenter_new_account, ac)

ac="AC-021-01"
print(f'{ac}: check scenter.py to register account')
if ac00201_setup_deploy_contracts and ac02001_scenter_new_account:
    ac02101_scenter_reg_account = ScenterRegTwoOptions(user1)
countResult(ac02101_scenter_reg_account, ac)

ac="AC-021-02"
print(f'{ac}: check scenter.py to register the same account second time')
if ac02101_scenter_reg_account:
    ac02102_scenter_reg_account_fail = ScenterRegTwoOptions(user1, True)
countResult(ac02102_scenter_reg_account_fail, ac)

ac="AC-022-01"
print(f'{ac}: check car.py to create new account')
ac02201_car_new_account = CarNewAccount()
countResult(ac02201_car_new_account, ac)

ac="AC-023-01"
print(f'{ac}: check car.py to provide account address')
ac02301_car_get_account = CarGetAccount(user2)
countResult(ac02301_car_get_account, ac)

ac="AC-024-01"
print(f'{ac}: check car.py to register account')
if ac00201_setup_deploy_contracts and ac02201_car_new_account:
    ac02401_car_reg_account = CarRegTwoOptions(user2)
countResult(ac02401_car_reg_account, ac)

ac="AC-024-02"
print(f'{ac}: check car.py to register the same account second time')
if ac02401_car_reg_account:
    ac02402_car_reg_account_fail = CarRegTwoOptions(user2, True)
countResult(ac02402_car_reg_account_fail, ac)

os.chdir(testsdir)

publishResultTotal()

sys.exit('Finished')

