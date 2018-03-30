./setup_test.sh 0.001
python vendor.py --reg AZA 1
batOut=$(python vendor.py --bat 1)
echo $batOut