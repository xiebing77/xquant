#!/usr/bin/python3
import sys
sys.path.append('../')
import argparse
from datetime import datetime
import uuid
import pprint
import utils.tools as ts
import common.xquant as xq
import common.log as log
from engine.backtestengine import BackTest
from common.overlap_studies import *
from common.price_transform import *
from common.momentum_indicators import *
from common.volume_indicators import *
from common.volatility_indicators import *
from common.cycle_indicators import *
from common.chart import chart
from db.mongodb import get_mongodb
from md.dbmd import DBMD

BACKTEST_INSTANCES_COLLECTION_NAME = 'bt_instances'

bt_db = get_mongodb('backtest')

def run(args):
    if not (args.m and args.sc and args.r):
        exit(1)

    instance_id = datetime.now().strftime("%Y%m%d-%H%M%S_") + str(uuid.uuid1())  # 每次回测都是一个独立的实例
    print('instance_id: %s' % instance_id)

    config = xq.get_strategy_config(args.sc)
    pprint.pprint(config)

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

    if args.chart:
        ordersets = []
        ordersets.append(engine.orders)
        chart(engine.md, engine.config, start_time, end_time, ordersets, args)


def get_instance(instance_id):
    if not (instance_id):
        exit(1)

    instances = bt_db.find(
        BACKTEST_INSTANCES_COLLECTION_NAME,
        {"instance_id": instance_id}
    )
    #print("instances: %s" % instances)
    if len(instances) <= 0:
        exit(1)
    instance = instances[0]
    return instance


def view(args):
    instance_id = args.sii
    instance = get_instance(instance_id)

    config = xq.get_strategy_config(instance['sc'])

    engine = BackTest(instance_id, instance['mds'], config)
    engine.view(config['symbol'], instance['orders'])


def analyze(args):
    instance_id = args.sii
    instance = get_instance(instance_id)
    print('marketing data src: %s  strategy config path: %s  ' % (instance['mds'], instance['sc']))

    config = xq.get_strategy_config(instance['sc'])
    pprint.pprint(config, indent=4)

    engine = BackTest(instance_id, instance['mds'], config)
    engine.analyze(config['symbol'], instance['orders'], args.hl, args.rmk)


def sub_cmd_chart(args):
    instance_id = args.sii
    instance = get_instance(instance_id)

    start_time = instance['start_time']
    end_time = instance['end_time']
    orders = instance['orders']

    md = DBMD(instance['mds'])
    md.tick_time = end_time
    config = xq.get_strategy_config(instance['sc'])
    ordersets = []
    ordersets.append(orders)
    chart(md, config, start_time, end_time, ordersets, args)


def sub_cmd_chart_diff(args):
    print(args.siis)
    print(len(args.siis))
    siis = args.siis
    if len(siis) != 2:
        exit(1)

    instance_a = get_instance(siis[0])
    instance_b = get_instance(siis[1])
    if instance_a['sc'] != instance_b['sc']:
        print(instance_a['sc'])
        print(instance_b['sc'])
        exit(1)

    start_time = min(instance_a['start_time'], instance_b['start_time'])
    end_time = max(instance_a['end_time'], instance_b['end_time'])
    orders_a = instance_a['orders']
    orders_b = instance_b['orders']

    md = DBMD(instance_a['mds'])
    md.tick_time = end_time
    config = xq.get_strategy_config(instance_a['sc'])
    ordersets = []
    ordersets.append(orders_a)
    ordersets.append(orders_b)
    chart(md, config, start_time, end_time, ordersets, args)



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
    parser.add_argument('--chart', help='chart', action="store_true")
    parser.add_argument('--log', help='log', action="store_true")
    add_argument_overlap_studies(parser)

    parser_view = subparsers.add_parser('view', help='view help')
    parser_view.add_argument('-sii', help='strategy instance id')
    parser_view.set_defaults(func=view)

    parser_analyze = subparsers.add_parser('analyze', help='analyze help')
    parser_analyze.add_argument('-sii', help='strategy instance id')
    parser_analyze.add_argument('--hl', help='high low', action="store_true")
    parser_analyze.add_argument('--rmk', help='remark', action="store_true")
    parser_analyze.set_defaults(func=analyze)

    parser_chart = subparsers.add_parser('chart', help='chart help')
    parser_chart.add_argument('-sii', help='strategy instance id')
    add_argument_overlap_studies(parser_chart)
    add_argument_price_transform(parser_chart)
    add_argument_momentum_indicators(parser_chart)
    add_argument_volume_indicators(parser_chart)
    add_argument_volatility_indicators(parser_chart)
    add_argument_cycle_indicators(parser_chart)
    parser_chart.set_defaults(func=sub_cmd_chart)

    parser_chart_diff = subparsers.add_parser('chart_diff', help='chart diff')
    parser_chart_diff.add_argument('-siis', nargs='*', help='strategy instance ids')
    add_argument_overlap_studies(parser_chart_diff)
    parser_chart_diff.set_defaults(func=sub_cmd_chart_diff)

    args = parser.parse_args()
    # print(args)
    if hasattr(args, 'func'):
        args.func(args)
    else:
        #parser.print_help()
        run(args)
