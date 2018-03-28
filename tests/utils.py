from platform import system
# from urllib.parse import urlparse
import os, sys
from subprocess import check_output, CalledProcessError, TimeoutExpired, STDOUT


def getIPCfilePath():
    cwd = os.getcwd()
    if system() == 'Windows':
        cwd_splitted = cwd.split('\\')[:-1]
        ipcfile = cwd_splitted[:]
        ipcfile.extend(['chain', 'data', 'geth.ipc'])

        ipc_file = 'file:////./pipe/' + '/'.join(ipcfile)
    else:
        cwd_splitted = cwd.split('/')[:-1]
        ipcfile = cwd_splitted[:]
        ipcfile.extend(['chain', 'data', 'geth.ipc'])
        ipc_file = 'file://' + '/'.join(ipcfile)
    return ipc_file


def setWeb3ProviderShellVariable(_ipcFile):
    os.environ["WEB3_PROVIDER_URI"] = _ipcFile


def getPythonInterpreter():
    return sys.executable


def runCmd(_args, _workdir=''):
    executed = False
    out = ""
    ext_args = _args[:]
    # this will initialize python_intrp when runCmd() will be run first time
    if not hasattr(runCmd, "python_intrp"):
        runCmd.python_intrp = getPythonInterpreter()
    ext_args.insert(0, runCmd.python_intrp)

    if len(_workdir) > 0:
        cwd = os.getcwd()
        os.chdir(_workdir)

    try:
        tmpout = check_output(ext_args, stderr=STDOUT, timeout=50)
    except CalledProcessError as ret:
        tmpout = ret.stdout
    except TimeoutExpired:
        tmpout = ''

    if len(_workdir) > 0:
        os.chdir(cwd)
    if len(tmpout) > 0:
        executed = True
        out = tmpout.decode().splitlines()

    return (executed, out)


def printError(_error, _cmdout=[]):
    if len(_cmdout) > 0:
        print('--- COMMAND RESPONSE:\n{}'.format("\n".join(_cmdout)))
    if type(_error) == str:
        print('--- ERROR:\n{}'.format(_error))
    else:
        print('--- ERROR:\n{}'.format("\n".join(_error)))


def checkOutput(_response, _clue, _inverted=False):
    if type(_clue) == str:
        cl = [_clue]
    else:
        cl = _clue[:]
    if not _inverted:
        res = False
        if len(_response) == len(_clue):
            res = True
            for i in range(len(_clue)):
                if _response[i] != _clue[i]:
                    res = False
        if not res:
            print('--- ACTUAL RESPONSE:\n{}\n--- EXPECTED RESPONSE:\n{}'.format("\n".join(_response), "\n".join(_clue)))
    else:
        res = True
        if len(_response) == len(_clue):
            for i in range(len(_clue)):
                if _response[i] == _clue[i]:
                    res = False
        if not res:
            print('--- ACTUAL RESPONSE:\n{}\n--- EXPECTED ANY RESPONSE EXCEPT:\n{}'.format("\n".join(_response),
                                                                                           "\n".join(_clue)))
    return res


def countResult(_res, _id,_read=False):
    if not hasattr(countResult, "sucessful"):
        countResult.sucessful = 0
    if not hasattr(countResult, "failed"):
        countResult.failed = 0
    if not hasattr(countResult, "list"):
        countResult.list = []
    if not _read:
        countResult.list.append({'ret': _res, 'id': _id})
        if _res:
            print("PASSED")
            countResult.sucessful += 1
        else:
            print("FAILED")
            countResult.failed += 1
    return (countResult.sucessful, countResult.failed, countResult.list)

totalResultFile = 'totalResults.csv'

def publishResultTotal():
    r = countResult(None, None, True)
    print('\nTotal tests run: {}\nFailed tests: {}'.format(r[0]+r[1], r[1]))
    safeResultsToCSV(r[2], totalResultFile)

def safeResultsToCSV(_results, _filepath):
    text = ""
    for res in _results:
        #print(res['id'], res['ret'])
        text += '{},{}\n'.format(res['id'], int(res['ret']))
    with open(_filepath, 'w') as file:
        file.write(text)


if __name__ == '__main__':
    print(getIPCfilePath())
    print(getPythonInterpreter())
    countResult(True)
    countResult(True)
    countResult(False)
    printTotal()
