#!/usr/bin/python3
import sys
sys.path.append('../')
import argparse
import common.xquant as xq
from common.instance import get_strategy_instance
from look import look


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='backtest')
    parser.add_argument('-sii', help='strategy instance id')
    parser.add_argument('--cs', help='chart show', action="store_true")
    args = parser.parse_args()
    # print(args)
    if not (args.sii):
        parser.print_help()
        exit(1)

    instance = get_strategy_instance(args.sii)
    config = xq.get_strategy_config(instance['config_path'])

    look(args.sii, config, instance['value'])

