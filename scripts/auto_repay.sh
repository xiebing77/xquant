#!/bin/bash


source ~/.profile
base_dir=$(cd `dirname $0`; pwd)
echo $1
python3.6 $base_dir/../tools/auto_repay.py -e binance >> $base_dir/auto_repay.log 2>&1
