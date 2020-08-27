#!/usr/bin/python3
import sys
sys.path.append('../')
import argparse
import os
import utils.tools as ts
import common.xquant as xq
import common.log as log
from engine.realengine import RealEngine


def real_run(config, instance_id, exchange_name, value, args):
    info = 'instance_id: %s,  exchange_name: %s, value: %s ' % (instance_id, exchange_name, value)
    print(info)
    module_name = config["module_name"].replace("/", ".")
    class_name = config["class_name"]

    if args.log:
        logfilename = instance_id + ".log"
        print(logfilename)

        server_ip = os.environ.get('LOG_SERVER_IP')
        server_port = os.environ.get('LOG_SERVER_PORT')
        print('Log server IP: %s, Log server port: %s' % (server_ip, server_port))

        log.init('real', logfilename, server_ip, server_port)
        log.info("%s" % (info))
        log.info("strategy name: %s;  config: %s" % (class_name, config))

    engine = RealEngine(instance_id, exchange_name, config, value, args.log)
    strategy = ts.createInstance(module_name, class_name, config, engine)

    engine.run(strategy, args.debug)


def real_view(config, instance_id, exchange_name, value):
    symbol = config['symbol']

    realEngine = RealEngine(instance_id, exchange_name, config, value)
    orders = realEngine.get_orders(symbol)
    realEngine.view(symbol, orders)

def real_analyze(config, instance_id, exchange_name, value, print_switch_hl, display_rmk):
    symbol = config['symbol']

    realEngine = RealEngine(instance_id, exchange_name, config, value)
    orders = realEngine.get_orders(symbol)
    realEngine.analyze(symbol, orders, print_switch_hl, display_rmk)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='real')
    parser.add_argument('-e', help='exchange')
    parser.add_argument('-sc', help='strategy config')
    parser.add_argument('-sii', help='strategy instance id')
    parser.add_argument('-v', type=int, help='value')
    parser.add_argument('--debug', help='debug', action="store_true")
    parser.add_argument('--log', help='log', action="store_true")
    args = parser.parse_args()
    print(args)
    if not (args.e and args.sc and args.sii and args.v):
        parser.print_help()
        exit(1)

    config = xq.get_strategy_config(args.sc)
    real_run(config, args.sii, args.e, args.v, args)
