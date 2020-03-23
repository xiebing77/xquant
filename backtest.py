#!/usr/bin/python3
import sys
sys.path.append('../')
import argparse
import json
import uuid
import utils.tools as ts
import common.xquant as xq
from engine.backtest import BackTest

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='backtest')
    parser.add_argument('-m', help='market data source')
    parser.add_argument('-sc', help='strategy config')
    parser.add_argument('-r', help='time range (2018-7-1T8' + xq.time_range_split + '2018-8-1T8)')
    parser.add_argument('--cs', help='chart show', action="store_true")
    args = parser.parse_args()
    # print(args)
    if not (args.m and args.sc and args.r):
        parser.print_help()
        exit(1)

    fo = open(args.sc, "r")
    config = json.loads(fo.read())
    fo.close()
    print("config: ", config)
    print("config[kline]: ", config['kline'])
    print("config[kline][interval]: ", config['kline']['interval'])

    module_name = config["module_name"].replace("/", ".")
    class_name = config["class_name"]
    start_time, end_time = ts.parse_date_range(args.r)
    instance_id = str(uuid.uuid1())  # 每次回测都是一个独立的实例

    engine = BackTest(instance_id, args.m, config)
    strategy = ts.createInstance(module_name, class_name, config, engine)
    engine.run(strategy, start_time, end_time, args.cs)
