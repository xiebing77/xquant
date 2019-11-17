#!/usr/bin/python3
import sys
sys.path.append('../')
import argparse
from exchange.binanceMargin import BinanceMargin
from decimal import Decimal

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='account')
    parser.add_argument('-e', help='exchange')
    args = parser.parse_args()
    # print(args)
    if not (args.e):
        parser.print_help()
        exit(1)

    if args.e == "binance":
        exchange = BinanceMargin(debug=True)
    else:
        print("exchange error!")
        exit(1)

    account = exchange.get_account()
    # print("account info: %s" % account)

    for i in account['balances']:
        debt = Decimal(i['interest']) + Decimal(i['borrowed'])
        asset = Decimal(i['free'])
        if debt > 0 and asset > 0:
            repay = min(debt, asset)
            print("Repay %s: %s" % (i['asset'], repay))
            # exchange.repay(i['asset'], repay)
