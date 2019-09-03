#!/usr/bin/python3
import sys
sys.path.append('../')
import argparse
from exchange.binanceExchange import BinanceExchange

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='account')
    parser.add_argument('-e', help='exchange')
    args = parser.parse_args()
    # print(args)
    if not (args.e and args.c):
        parser.print_help()
        exit(1)

    if args.e == "binance":
        exchange = BinanceExchange(debug=True)
    else:
        print("exchange error!")
        exit(1)

    coins = args.c.split(",")
    account = exchange.get_account(coins)
    print("account info: %s" % account)
