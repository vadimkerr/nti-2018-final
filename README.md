These set of files is intended to perform automatic testing of "first day" User Stories.

1. Put the code of your implementation of scripts and contracts into `src` directory. Put there 
   your python modules (if any), implementation of you contracts and all other
   artefacts of you solution.

   Please note that your solution must use automatic Web3 provider discovery mechanism.
   It assumes that `WEB3_PROVIDER_URI` environment variable is set before scripts is run.
   is run. For example,

On Linux:
```
$ env WEB3_PROVIDER_URI='http://127.0.0.1:8545' ./setup.py --setup 0.9
```

On Windows:
```
set WEB3_PROVIDER_URI='file:////./pipe/C:/privatechain/geth.ipc'
c:\Anaconda3\python.exe car.py --new
```

2. To check that the implementation is compatible with automatic testing system
   use `do_test` script. It requires path to ethereum-go client (geth)
   and python interpeter with `web3.py` library set up in the environment.
   Please note that
   - a private proof-of-authority node is set up automatically before the scripts are
     run. It contains a set of pre-configured accounts which will be provided
     to your solution by changing 'account.json' file.
   - the node is run with `miner` process turned off in order to reduce cpu resources
     usage, the test script is responsible to turn the transaction validation and
     block sealing process when it is required by tests.
   - the test script sets up `WEB3_PROVIDER_URI` prior to invoke scripts
     from `src` directory.
   - if your solution uses py-solc module to complile Solidity contracts please
     make sure that directory containing `solc` tool is in PATH environment variable
     or `SOLC_BINARY` is set prior to `do_test` is run.
   
   Below you can find different examples to run `do_tests`:

On Linux, py-solc is not used or `solc` is in PATH:
```
$ ./do_test.sh /opt/geth/geth /opt/anaconda3/bin/python
```

On Linux, specify path to `solc` explicitly:
```
$ env SOLC_BINARY=/opt/solidity/solc ./do_test.sh /opt/geth/geth /opt/anaconda3/bin/python
```

On Windows:
```
do_test.cmd "c:\Program Files\Geth\geth.exe" "c:\Anaconda3\python.exe"
```

4. Look at the passed and failed tests to find how close you to the final solution.
