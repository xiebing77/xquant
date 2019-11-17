#!/usr/bin/env bash

OS=`uname -s`
if [ ${OS} == "Darwin" ];then
    source ~/.bash_profile
elif [ ${OS} == "Linux" ]; then
    source ~/.profile
fi

base_dir=$(cd `dirname $0`; pwd)
echo $1
PYTHONPATH=$base_dir python3 $base_dir/../tools/auto_repay.py -e binance >> $base_dir/auto_repay.log 2>&1
