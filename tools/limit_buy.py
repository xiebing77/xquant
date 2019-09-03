#!/usr/bin/python3
import sys
sys.path.append('../')
import argparse
from exchange.binanceExchange import BinanceExchange
import common.xquant as xq

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='account')
    parser.add_argument('-e', help='exchange')
    parser.add_argument('-s', help='symbol (btc_usdt)')
    parser.add_argument('-p', help='price')
    parser.add_argument('-a', help='amount')
    args = parser.parse_args()
    # print(args)
    if not (args.e and args.s and args.p and args.a):
        parser.print_help()
        exit(1)

    if args.e == "binance":
        exchange = BinanceExchange(debug=True)
    else:
        print("exchange error!")
        exit(1)

    exchange.send_order(xq.DIRECTION_LONG, xq.OPEN_POSITION, xq.ORDER_TYPE_LIMIT, args.s, float(args.p), float(args.a))
