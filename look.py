#!/usr/bin/python3
import sys
sys.path.append('../')
import argparse
import json
import uuid
import utils.tools as ts
import common.xquant as xq
import common.log as log
from engine.engine import Engine
from setup import *

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='backtest')
    parser.add_argument('-sc', help='strategy config')
    parser.add_argument('-sii', help='strategy instance id')
    parser.add_argument('-v', type=int, help='value')
    parser.add_argument('--cs', help='chart show', action="store_true")
    args = parser.parse_args()
    # print(args)
    if not (args.sc and args.sii and args.v):
        parser.print_help()
        exit(1)

    fo = open(args.sc, "r")
    config = json.loads(fo.read())
    fo.close()
    print("config: ", config)


    symbol = config["symbol"]
    instance_id = args.sii

    engine = Engine(instance_id, config, args.v, db_order_name)
    orders = engine.td_db.find("orders", {"instance_id": instance_id})
    engine.analyze(symbol, orders)

   # if display_switch:
    #interval = strategy.config["kline"]["interval"]
    #klines = self.get_klines(symbol, interval, (end_time - start_time).total_seconds()/xq.get_interval_seconds(interval))
    #self.display(symbol, orders, klines)

