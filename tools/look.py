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


def look(instance_id, config, value):
    engine = Engine(instance_id, config, value, db_order_name)
    orders = engine.td_db.find("orders", {"instance_id": instance_id})
    engine.analyze(config["symbol"], orders)


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

    config = xq.get_strategy_config(args.sc)

    look(args.sii, config, args.v)

