./setup_test.sh 0.001
python vendor.py --reg AZA 1

batOut1=$(python vendor.py --bat 1)
batId1=${batOut1: -40}

batOut2=$(python vendor.py --bat 1)
batId2=${batOut2: -40}

python car.py --new

carAddr=$(python car.py --account)
command='geth --exec "eth.sendTransaction({from:eth.accounts[0], to: '
command+="'$carAddr'"
command+=', value: 1000000000000000000000})" attach http://127.0.0.1:8545'
transaction=$(eval $command)

python car.py --reg


echo python scenter.py --new "pass"
scAddr=$(python scenter.py --new "pass")
command='geth --exec "eth.sendTransaction({from:eth.accounts[0], to: '
command+="'$scAddr'"
command+=', value: 1000000000000000000000})" attach http://127.0.0.1:8545'
transaction=$(eval $command)
echo Created and funded address: $scAddr

echo python scenter.py --reg
python scenter.py --reg


python vendor.py --owner $batId1 $carAddr
python vendor.py --owner $batId2 $scAddr

echo $batId2 $batId1 $carAddr 100