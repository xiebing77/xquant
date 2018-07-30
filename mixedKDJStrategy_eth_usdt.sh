#!/bin/bash

# -a target amount digits
# -d base amount digits
# -p price digits
# -g price gap
# -n price gap num
# -r target coin reserve
# -s base coin reserve
# -e exchange name

source ~/.profile
base_dir=$(cd `dirname $0`; pwd)

python3.6 $base_dir/mixedKDJStrategy.py -symbol eth_usdt -digits '{"eth":8,"usdt":2}' -e binance -s 600 -limit 20 -i 1
