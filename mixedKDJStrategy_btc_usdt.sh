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

python3.6 $base_dir/mixedKDJStrategy.py -symbol btc_usdt -digits '{"btc":8,"usdt":2}' -e binance -s 600 -limit 200 -i 1
