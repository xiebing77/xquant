#!/usr/bin/python3
import sys
sys.path.append('../')
import argparse
from exchange.binanceExchange import BinanceExchange

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='balance')
    parser.add_argument('-e', help='exchange')
    args = parser.parse_args()
    # print(args)
    if not (args.e):
        parser.print_help()
        exit(1)

    if args.e == "binance":
        exchange = BinanceExchange(debug=True)
    else:
        print("exchange error!")
        exit(1)

    balances = exchange.get_balances()
    print("balances: %s" % balances)
