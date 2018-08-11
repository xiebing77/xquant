#!/bin/bash


source ~/.profile
base_dir=$(cd `dirname $0`; pwd)
echo $1
python3.6 $base_dir/main.py strategy/mixedkdj MixedKDJStrategy '{"symbol":"btc_usdt", "digits":{"btc":8,"usdt":2}, "exchange":"binance", "sec": 600, "limit":200, "id": "x12"}' $1
