#!/usr/bin/python3
import sys
sys.path.append('../')
import argparse
import common.xquant as xq
from common.instance import get_strategy_instance
from real import real_run

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='real')
    parser.add_argument('-sii', help='strategy instance id')
    parser.add_argument('--debug', help='debug', action="store_true")
    parser.add_argument('--log', help='log', action="store_true")
    args = parser.parse_args()
    print(args)
    if not (args.sii):
        parser.print_help()
        exit(1)

    instance = get_strategy_instance(args.sii)

    config = xq.get_strategy_config(instance['config_path'])
    real_run(config, args.sii, instance['exchange'], instance['value'], args)
