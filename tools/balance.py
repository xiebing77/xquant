#!/usr/bin/python3
import sys
sys.path.append('../')
import argparse
from exchange.binanceExchange import BinanceExchange
from exchange.binanceMargin import BinanceMargin

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='account')
    parser.add_argument('-e', help='exchange, eg: binance, binance_margin')
    args = parser.parse_args()
    # print(args)
    if not (args.e):
        parser.print_help()
        exit(1)

    if args.e == "binance":
        exchange = BinanceExchange(debug=True)
    elif args.e == "binance_margin":
        exchange = BinanceMargin(debug=True)
    else:
        print("exchange error!")
        exit(1)

    account = exchange.get_account()
    print("account info: %s" % account)
