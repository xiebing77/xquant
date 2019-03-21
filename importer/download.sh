#!/bin/bash

#source ~/.profile
range=2019-3-14~2019-3-21
echo $range

symbles=(btc_usdt bnb_usdt eth_usdt)
echo ${symbles[*]}

kline_types=(1m 5m 15m 30m 1h 2h 4h 6h 12h 1d)
echo ${kline_types[*]}

for symble in ${symbles[*]}
do
    #echo $symble

    for kline_type in ${kline_types[*]}
    do
        #echo $kline_type
        echo "downloading  ${range}  ${symble}  ${kline_type}"
        python3.6 binance.py -r $range -s $symble -k $kline_type
    done
done
