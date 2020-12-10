#!/usr/bin/python3
import sys
sys.path.append('../')
import argparse
import common.xquant as xq
from common.instance import get_strategy_instance
from real import real_run
from real import real_view
from real import real_analyze
from db.mongodb import get_mongodb
import setup
from pprint import pprint


def real2_run(args):
    instance = get_strategy_instance(args.sii)
    config = xq.get_strategy_config(instance['config_path'])

    real_run(config, args.sii, instance['exchange'], instance['value'], args)

def real2_view(args):
    instance = get_strategy_instance(args.sii)
    config = xq.get_strategy_config(instance['config_path'])

    real_view(config, args.sii, instance['exchange'], instance['value'])

def real2_analyze(args):
    instance = get_strategy_instance(args.sii)
    config = xq.get_strategy_config(instance['config_path'])

    real_analyze(config, args.sii, instance['exchange'], instance['value'], args.hl, args.rmk)


def real2_list(args):
    td_db = get_mongodb(setup.trade_db_name)
    ss = td_db.find("strategies", {"user": args.user})
    #pprint(ss)
    s_fmt = "%-30s  %10s    %-60s  %-20s"
    print(s_fmt % ("instance_id", "value", "config_path", "exchange"))
    for s in ss:
        print(s_fmt % (s["instance_id"], s["value"], s["config_path"], s["exchange"]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='real')
    parser.add_argument('-sii', help='strategy instance id')
    parser.add_argument('--debug', help='debug', action="store_true")
    parser.add_argument('--log', help='log', action="store_true")

    subparsers = parser.add_subparsers(help='sub-command help')

    parser_view = subparsers.add_parser('view', help='view help')
    parser_view.add_argument('-sii', help='strategy instance id')
    parser_view.set_defaults(func=real2_view)

    parser_analyze = subparsers.add_parser('analyze', help='analyze help')
    parser_analyze.add_argument('-sii', help='strategy instance id')
    parser_analyze.add_argument('--hl', help='high low', action="store_true")
    parser_analyze.add_argument('--rmk', help='remark', action="store_true")
    parser_analyze.set_defaults(func=real2_analyze)

    parser_list = subparsers.add_parser('list', help='list of strateay')
    parser_list.add_argument('-user', help='user name')
    parser_list.set_defaults(func=real2_list)

    args = parser.parse_args()
    #print(args)

    if hasattr(args, 'func'):
        args.func(args)
    else:
        real2_run(args)
