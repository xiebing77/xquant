#!/usr/bin/python3
import sys
sys.path.append('../')
import argparse
from exchange.exchange import create_exchange

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='trade')
    parser.add_argument('-e', help='exchange')
    parser.add_argument('-s', help='symbol (btc_usdt)')
    args = parser.parse_args()
    # print(args)
    if not (args.e and args.s):
        parser.print_help()
        exit(1)

    exchange = create_exchange(args.e)
    if not exchange:
        print("exchange error!")
        exit(1)
    exchange.connect()

    trades = exchange.get_trades(args.s)
    print("trades: %s" % trades)
