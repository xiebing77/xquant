#!/bin/bash

#source ~/.profile
range=$1
echo $range

mds=(binance)
echo ${mds[*]}

symbles=(btc_usdt bnb_usdt eth_usdt btc_pax)
echo ${symbles[*]}

kline_types=(1m 5m 15m 30m 1h 2h 4h 6h 8h 12h 1d)
echo ${kline_types[*]}

for md in ${mds[*]}
do
    for symble in ${symbles[*]}
    do
        #echo $symble

        for kline_type in ${kline_types[*]}
        do
            #echo $kline_type
            echo "downloading  ${range}  ${md}  ${symble}  ${kline_type}"
            if [ $range ]
            then
                python3.6 download.py -m $md -s $symble -k $kline_type -r $range
            else
                python3.6 download.py -m $md -s $symble -k $kline_type
            fi
        done
    done
done