@echo off

set gethbin=%1
if "%~1" == "" set gethbin="c:\Program Files\Geth\geth.exe"

set pythonbin=%2
if "%~2" == "" set pythonbin="C:\Program Files (x86)\Microsoft Visual Studio\Shared\Anaconda3_64\python.exe"

%pythonbin% -c "import web3; import sys ; sys.exit(1) if web3.__version__[0] != '4' else sys.exit(0)"

echo Checking version of web3.py python library...
if errorlevel 1 exit /b 1

if "%SOLC_BINARY%"=="" echo WARNING
if "%SOLC_BINARY%"=="" echo The environment variable SOLC_BINARY is not set.
if "%SOLC_BINARY%"=="" echo If your solution uses py-solc to build Solidity artefacts
if "%SOLC_BINARY%"=="" echo please make sure that "solc" is available through PATH
if "%SOLC_BINARY%"=="" echo or set SOLC_BINARY in "Control Panel" - "System" - "Advanced
if "%SOLC_BINARY%"=="" echo system settings"

cd chain

echo Test chain is being deployed...

start "TESTBEDGETH" start.cmd %gethbin%

rem **** HACK - wait for 5 seconds o_O ****
ping 127.0.0.1 -n 6 -w 1000 > NUL

cd ..\tests

echo Tests running...

%pythonbin% test.py

echo Test chain is shuting down...

taskkill.exe /fi "WINDOWTITLE eq TESTBEDGETH*" > NUL

cd ..
