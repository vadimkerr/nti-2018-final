echo python scenter.py --new "pass"
address=$(python scenter.py --new "pass")
command='geth --exec "eth.sendTransaction({from:eth.accounts[0], to: '
command+="'$address'"
command+=', value: 1000000000000000000000})" attach http://127.0.0.1:8545'
transaction=$(eval $command)
echo Created and funded address: $address
echo
echo python scenter.py --reg
python scenter.py --reg