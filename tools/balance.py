#!/usr/bin/python3
import sys
sys.path.append('../')
import argparse
from exchange.exchange import create_exchange
from tabulate import tabulate as tb
import pprint

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='account')
    parser.add_argument('-e', help='exchange, eg: binance, binance_margin')
    args = parser.parse_args()
    # print(args)
    if not (args.e):
        parser.print_help()
        exit(1)

    exchange = create_exchange(args.e)
    if not exchange:
        print("exchange error!")
        exit(1)

    account = exchange.get_account()
    print("account info:" )
    #pprint.pprint(account)
    print(tb(account['balances']))
