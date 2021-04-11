#!/bin/bash

#source ~/.profile
range=$1
echo $range

mds=(binance)
echo ${mds[*]}

symbles=btc_usdt,eth_usdt,btc_busd,btc_usdc
echo ${symbles}

kline_types=1m,5m,15m,30m,1h,2h,4h,6h,8h,12h,1d
echo ${kline_types}

for md in ${mds[*]}
do

    #echo $kline_type
    echo "downloading  ${range}  ${md}"
    if [ $range ]
    then
        python3 download2.py -m $md -ss $symbles -kts $kline_types -r $range
    else
        python3 download2.py -m $md -ss $symbles -kts $kline_types
    fi

done