#!/usr/bin/python3
import sys
sys.path.append('../')
import argparse
import uuid
import utils.tools as ts
import common.xquant as xq
import common.log as log
from engine.backtest import BackTest
from common.overlap_studies import *
from db.mongodb import get_mongodb

BACKTEST_INSTANCES_COLLECTION_NAME = 'bt_instances'

bt_db = get_mongodb('backtest')

def run(args):
    if not (args.m and args.sc and args.r):
        exit(1)

    instance_id = str(uuid.uuid1())  # 每次回测都是一个独立的实例
    print('instance_id: %s' % instance_id)

    config = xq.get_strategy_config(args.sc)

    module_name = config["module_name"].replace("/", ".")
    class_name = config["class_name"]

    symbol = config['symbol']
    time_range = args.r
    start_time, end_time = ts.parse_date_range(time_range)

    if args.log:
        logfilename = class_name + "_"+ symbol + "_" + time_range + "_" + instance_id + ".log"
        print(logfilename)
        log.init("backtest", logfilename)
        log.info("strategy name: %s;  config: %s" % (class_name, config))


    engine = BackTest(instance_id, args.m, config)
    strategy = ts.createInstance(module_name, class_name, config, engine)
    engine.run(strategy, start_time, end_time)
    engine.analyze(symbol, engine.orders)
    _id = bt_db.insert_one(
        BACKTEST_INSTANCES_COLLECTION_NAME,
        {
            "instance_id": instance_id,
            "start_time": start_time,
            "end_time": end_time,
            "orders": engine.orders,
            "mds": args.m,
            "sc": args.sc,
        },
    )

    if args.cs:
        engine.show(symbol, start_time, end_time, args)


def show(args):
    if not (args.sii):
        exit(1)

    instance_id = args.sii

    print(instance_id)
    instances = bt_db.find(
        BACKTEST_INSTANCES_COLLECTION_NAME,
        {"instance_id": instance_id}
    )
    #print("instances: %s" % instances)
    if len(instances) <= 0:
        exit(1)
    instance = instances[0]
    mds = instance['mds']
    sc = instance['sc']
    print('instance_id: %s  marketing data src: %s  strategy config path: %s  ' % (instance_id, mds, sc))

    config = xq.get_strategy_config(sc)
    symbol = config['symbol']
    start_time = instance['start_time']
    end_time = instance['end_time']
    orders = instance['orders']

    engine = BackTest(instance_id, mds, config)
    engine.md.tick_time = end_time
    engine.orders = orders
    engine.show(symbol, start_time, end_time, args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='backtest')

    subparsers = parser.add_subparsers(help='sub-command help')

    """
    parser_run = subparsers.add_parser('run', help='run help')
    parser_run.add_argument('-m', help='market data source')
    parser_run.add_argument('-sc', help='strategy config')
    parser_run.add_argument('-r', help='time range (2018-7-1T8' + xq.time_range_split + '2018-8-1T8)')
    parser_run.add_argument('--cs', help='chart show', action="store_true")
    parser_run.add_argument('--log', help='log', action="store_true")
    add_argument_overlap_studies(parser_run)
    parser_run.set_defaults(func=run)
    """
    parser.add_argument('-m', help='market data source')
    parser.add_argument('-sc', help='strategy config')
    parser.add_argument('-r', help='time range (2018-7-1T8' + xq.time_range_split + '2018-8-1T8)')
    parser.add_argument('--cs', help='chart show', action="store_true")
    parser.add_argument('--log', help='log', action="store_true")
    add_argument_overlap_studies(parser)

    parser_show = subparsers.add_parser('show', help='show help')
    parser_show.add_argument('-sii', help='strategy instance id')
    add_argument_overlap_studies(parser_show)
    parser_show.set_defaults(func=show)

    args = parser.parse_args()
    print(args)
    if hasattr(args, 'func'):
        args.func(args)
    else:
        #parser.print_help()
        run(args)
