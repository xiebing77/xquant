#!/bin/bash

source ~/.profile
base_dir=$(cd `dirname $0`; pwd)
echo $1
python3.6 $base_dir/main.py strategy/kdj KDJStrategy \
    '{"symbol":"btc_usdt", "sec": 600}' \
    '{
        "limit":{"value":100, "mode":0}, 
        "digits":{"btc":6,"usdt":2}, 
        "select":"backtest", 
        "real":{"instance_id": "x11", "exchange":"binance"}, 
        "backtest":{"start_time":"2018-08-10 00:00:00", "end_time":"2018-08-11 00:00:00"}}' \
    $1
