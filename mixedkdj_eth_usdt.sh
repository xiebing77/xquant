#!/bin/bash

source ~/.profile
base_dir=$(cd `dirname $0`; pwd)
echo $1
python3.6 $base_dir/main.py strategy/mixedkdj MixedKDJStrategy '{"symbol":"eth_usdt", "digits":{"eth":8,"usdt":2}, "exchange":"binance", "sec": 600, "limit":100, "id": "x20"}' $1