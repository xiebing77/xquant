#!/usr/bin/python3
import sys
sys.path.append('../')
import argparse
from exchange.exchange import create_exchange, exchange_names
from tabulate import tabulate as tb
import pprint


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='account infomation')
    parser.add_argument('-exchange', choices=exchange_names, help='exchange name')
    args = parser.parse_args()
    # print(args)
    if not (args.exchange):
        parser.print_help()
        exit(1)

    exchange = create_exchange(args.exchange)
    if not exchange:
        print("exchange name error!")
        exit(1)
    exchange.connect()

    account = exchange.get_account()
    print("account info:" )
    pprint.pprint(account)
