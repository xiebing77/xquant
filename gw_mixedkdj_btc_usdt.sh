#!/bin/bash


source ~/.profile
base_dir=$(cd `dirname $0`; pwd)
echo $1
python3.6 $base_dir/main.py strategy/mixedkdj MixedKDJStrategy \
    '{"symbol":"btc_usdt", "sec": 180}' \
    '{
        "limit":{"value":1000, "mode":0}, 
        "exchange":"binance",
        "commission_rate": 0.001,
        "digits":{"btc":6,"usdt":2},
        "select":"real",
        "real":{"instance_id": "MixedKDJStrategy_btc_usdt_gwbtc"},
        "backtest":{"start_time":"2018-07-10 00:00:00", "end_time":"2018-08-11 00:00:00"}}' \
    
