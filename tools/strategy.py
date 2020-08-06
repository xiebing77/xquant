#!/usr/bin/python3
import json
import argparse
import sys
sys.path.append('../')
from common.instance import add_strategy_instance, update_strategy_instance, delete_strategy_instance, get_strategy_instance

"""
python3 strategy.py -m add -sii gwEma2BtcUsdt -p '{"user":"gw", "exchange" : "binance_margin","config_path" : "/home/gw/margin/xq/config/ema/ema2_btc_usdt_1d.jsn","value" : 10000}'
python3 strategy.py -m update -sii gwEma2BtcUsdt -p '{"value" : 18000}'
python3 strategy.py -m delete -sii gwEma2BtcUsdt
python3 strategy.py -m show -sii gwEma2BtcUsdt
"""
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Strategy Operation')
    parser.add_argument('-m', help='Mode: add, delete, update')
    parser.add_argument('-sii', help='Instance ID')
    parser.add_argument('-p', help='Parameters')
    args = parser.parse_args()

    print(args)

    if not args.m and not args.sii:
        parser.print_help()
        exit(1)

    if args.m == 'add' and not args.p:
        parser.print_help()
        exit(1)

    if args.m == 'udpate' and not args.p:
        parser.print_help()
        exit(1)

    if args.m == 'add':
        add_strategy_instance({**{"instance_id": args.sii}, **json.loads(args.p)})
    elif args.m == 'update':
        update_strategy_instance({"instance_id": args.sii}, json.loads(args.p))
    elif args.m == 'delete':
        delete_strategy_instance({"instance_id": args.sii})
    elif args.m == 'show':
        print(get_strategy_instance(args.sii))
    else:
        parser.print_help()
        exit(1)

    exit(1)
