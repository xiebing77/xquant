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

python3.6 $base_dir/main.py strategy/mixedKDJStrategy MixedKDJStrategy '{"symbol":"btc_usdt", "digits":{"btc":8,"usdt":2}, "exchange":"binance", "sec": 600, "limit":200, "id": "xb2"}'
