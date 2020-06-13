#!/usr/bin/python3
import sys
sys.path.append('../')
import argparse
import common.xquant as xq
from common.instance import get_strategy_instance
from real import real_run
from real import real_view


def real2_run(args):
    instance = get_strategy_instance(args.sii)
    config = xq.get_strategy_config(instance['config_path'])

    real_run(config, args.sii, instance['exchange'], instance['value'], args)

def real2_view(args):
    instance = get_strategy_instance(args.sii)
    config = xq.get_strategy_config(instance['config_path'])

    real_view(config, args.sii, instance['exchange'], instance['value'])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='real')
    parser.add_argument('-sii', help='strategy instance id')
    parser.add_argument('--debug', help='debug', action="store_true")
    parser.add_argument('--log', help='log', action="store_true")

    subparsers = parser.add_subparsers(help='sub-command help')
    parser_view = subparsers.add_parser('view', help='view help')
    parser_view.add_argument('-sii', help='strategy instance id')
    parser_view.set_defaults(func=real2_view)

    args = parser.parse_args()
    #print(args)
    if not (args.sii):
        parser.print_help()
        exit(1)

    if hasattr(args, 'func'):
        args.func(args)
    else:
        real2_run(args)
