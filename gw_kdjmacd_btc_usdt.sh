#!/bin/bash


#source ~/.profile
base_dir=$(cd `dirname $0`; pwd)
echo $1
python3.6 $base_dir/main.py strategy/kdjmacd KDJMACDStrategy \
    '{"symbol":"btc_usdt", "sec": 180}' \
    '{
        "limit":{"value":1000, "mode":1}, 
        "exchange":"binance",
        "commission_rate": 0.001,
        "digits":{"btc":6,"usdt":2},
        "select":"real",
        "real":{"instance_id": "gw_kdjmacd"},
        "backtest":{"start_time":"2018-08-10 00:00:00", "end_time":"2018-09-06 00:00:00"}}' \
    $1
