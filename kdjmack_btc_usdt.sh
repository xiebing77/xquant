#!/bin/bash


#source ~/.profile
base_dir=$(cd `dirname $0`; pwd)
echo $1
python3.6 $base_dir/main.py strategy/kdjmacd KDJMACDStrategy \
    '{"symbol":"btc_usdt", "sec": 600}' \
    '{
        "limit":{"value":100, "mode":0}, 
        "exchange":"binance",
        "commission_rate": 0.001,
        "digits":{"btc":6,"usdt":2},
        "select":"backtest",
        "real":{"instance_id": "x12"},
        "backtest":{"start_time":"2018-03-01 00:00:00", "end_time":"2018-06-01 00:00:00"}}' \
    $1
