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
from exchange.exchange import BINANCE_SPOT_EXCHANGE_NAME
from engine.backtestengine import BackTest
from chart.chart import chart, chart_add_all_argument
from db.mongodb import get_mongodb
from md.dbmd import DBMD

BACKTEST_INSTANCES_COLLECTION_NAME = 'bt_instances'

bt_db = get_mongodb('backtest')

def create_instance_id():
    instance_id = datetime.now().strftime("%Y%m%d-%H%M%S_") + str(uuid.uuid1())  # 每次回测都是一个独立的实例
    print('new id of instance: %s' % instance_id)
    return instance_id

def run(args):
    if not (args.m and args.sc and args.r):
        exit(1)

    instance_id = create_instance_id()

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
    engine.analyze(symbol, engine.orders, True, args.rmk)
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


def sub_cmd_refresh(args):
    instance_id = args.sii
    instance = get_instance(instance_id)
    print('marketing data src: %s  strategy config path: %s  ' % (instance['mds'], instance['sc']))

    config = xq.get_strategy_config(instance['sc'])
    pprint.pprint(config, indent=4)

    engine = BackTest(instance_id, instance['mds'], config)
    module_name = config["module_name"].replace("/", ".")
    class_name = config["class_name"]
    strategy = ts.createInstance(module_name, class_name, config, engine)
    engine.refresh(strategy, [ datetime.fromtimestamp(order["create_time"]) for order in instance['orders']])
    orders = engine.orders
    for idx, order in enumerate(engine.orders):
        old_order = instance['orders'][idx]
        if "high" in old_order:
            order["high"] = old_order["high"]
            order["high_time"] = old_order["high_time"]
            order["low"] = old_order["low"]
            order["low_time"] = old_order["low_time"]
    engine.analyze(config['symbol'], engine.orders, True, True)


def sub_cmd_chart(args):
    instance_id = args.sii
    instance = get_instance(instance_id)

    start_time = instance['start_time']
    end_time = instance['end_time']
    orders = instance['orders']

    md = DBMD(instance['mds'])
    md.tick_time = end_time

    config = xq.get_strategy_config(instance['sc'])
    symbol = config["symbol"]
    interval = config["kline"]["interval"]
    title = symbol + '  ' + config['kline']['interval'] + ' ' + config['class_name']

    ordersets = []
    ordersets.append(orders)

    chart(title, md, symbol, interval, start_time, end_time, ordersets, args)


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
    symbol = config["symbol"]
    interval = config["kline"]["interval"]
    title = symbol + '  ' + config['kline']['interval'] + ' ' + config['class_name']

    ordersets = []
    ordersets.append(orders_a)
    ordersets.append(orders_b)

    chart(title, md, symbol, interval, start_time, end_time, ordersets, args)


def sub_cmd_merge(args):
    print(args.siis)
    print(len(args.siis))
    siis = args.siis
    if len(siis) != 2:
        exit(1)

    instance_a = get_instance(siis[0])
    instance_b = get_instance(siis[1])

    sc = instance_a['sc']
    if sc != instance_b['sc']:
        print(instance_a['sc'])
        print(instance_b['sc'])
        exit(1)

    mds = instance_a['mds']
    if mds != instance_b['mds']:
        print(instance_a['mds'])
        print(instance_b['mds'])
        exit(1)

    start_time = min(instance_a['start_time'], instance_b['start_time'])
    end_time = max(instance_a['end_time'], instance_b['end_time'])

    orders_a = instance_a['orders']
    orders_b = instance_b['orders']
    if instance_a['start_time'] < instance_b['start_time']:
        orders = orders_a + orders_b
    else:
        orders = orders_b + orders_a

    _id = bt_db.insert_one(
        BACKTEST_INSTANCES_COLLECTION_NAME,
        {
            "instance_id": create_instance_id(),
            "start_time": start_time,
            "end_time": end_time,
            "orders": orders,
            "mds": mds,
            "sc": sc,
        },
    )


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
    parser.add_argument('-m', default=BINANCE_SPOT_EXCHANGE_NAME, help='market data source')
    parser.add_argument('-sc', help='strategy config')
    parser.add_argument('-r', help='time range (2018-7-1T8' + xq.time_range_split + '2018-8-1T8)')
    parser.add_argument('--chart', help='chart', action="store_true")
    parser.add_argument('--log', help='log', action="store_true")
    parser.add_argument('--rmk', help='remark', action="store_true")

    parser_view = subparsers.add_parser('view', help='view help')
    parser_view.add_argument('-sii', help='strategy instance id')
    parser_view.set_defaults(func=view)

    parser_analyze = subparsers.add_parser('analyze', help='analyze help')
    parser_analyze.add_argument('-sii', help='strategy instance id')
    parser_analyze.add_argument('--hl', help='high low', action="store_true")
    parser_analyze.add_argument('--rmk', help='remark', action="store_true")
    parser_analyze.set_defaults(func=analyze)

    parser_refresh = subparsers.add_parser('refresh', help='refresh order info')
    parser_refresh.add_argument('-sii', help='strategy instance id')
    parser_refresh.set_defaults(func=sub_cmd_refresh)

    parser_chart = subparsers.add_parser('chart', help='chart help')
    parser_chart.add_argument('-sii', help='strategy instance id')
    parser_chart.add_argument('--volume', action="store_true", help='volume')
    chart_add_all_argument(parser_chart)
    parser_chart.set_defaults(func=sub_cmd_chart)

    parser_chart_diff = subparsers.add_parser('chart_diff', help='chart diff')
    parser_chart_diff.add_argument('-siis', nargs='*', help='strategy instance ids')
    parser_chart_diff.add_argument('--volume', action="store_true", help='volume')
    chart_add_all_argument(parser_chart_diff)
    parser_chart_diff.set_defaults(func=sub_cmd_chart_diff)

    parser_merge = subparsers.add_parser('merge', help='merge')
    parser_merge.add_argument('-siis', nargs='*', help='strategy instance ids')
    parser_merge.set_defaults(func=sub_cmd_merge)

    args = parser.parse_args()
    # print(args)
    if hasattr(args, 'func'):
        args.func(args)
    else:
        #parser.print_help()
        run(args)
