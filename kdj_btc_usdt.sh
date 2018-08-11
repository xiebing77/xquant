#!/bin/bash

source ~/.profile
base_dir=$(cd `dirname $0`; pwd)
echo $1
python3.6 $base_dir/main.py strategy/kdj KDJStrategy '{"symbol":"btc_usdt", "digits":{"btc":6,"usdt":2}, "exchange":"binance", "sec": 600, "limit":200, "id": "x11"}' $1
