#!/usr/bin/python3
import sys
sys.path.append('../')
import argparse
import json
import uuid
import utils.tools as ts
import common.xquant as xq
import common.log as log
from engine.backtest import BackTest
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

    module_name = config["module_name"].replace("/", ".")
    class_name = config["class_name"]

    engine = Display(args.sii, config)
    strategy = ts.createInstance(module_name, class_name, config, engine)

    engine.value = args.v
    engine.run(strategy, db_order_name)
