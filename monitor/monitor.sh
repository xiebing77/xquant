#!/bin/bash


source ~/.profile
base_dir=$(cd `dirname $0`; pwd)
echo $1
python3.6 $base_dir/monitor.py -r pkguowu@yahoo.com -f ~/xq/gbtc.log
