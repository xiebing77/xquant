#!/usr/bin/python3
import sys
sys.path.append('../')
import argparse
from exchange.exchange import create_exchange, exchange_names
from tabulate import tabulate as tb
import pprint

from common.xquant import creat_symbol, get_balance_free, get_balance_frozen


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='account infomation')
    parser.add_argument('-exchange', choices=exchange_names, help='exchange name')
    parser.add_argument('-basecoin', default='usdt', help='assert sum by base coin')
    args = parser.parse_args()
    # print(args)
    if not (args.exchange):
        parser.print_help()
        exit(1)

    exchange = create_exchange(args.exchange)
    if not exchange:
        print("exchange name error!")
        exit(1)

    balances = exchange.get_all_balances()
    print("balances info:" )
    print(tb(balances))

    for index, value in enumerate(exchange.get_kline_column_names()):
        if value == "close":
            closeindex = index
            break

    total_value = 0
    for coin in balances:
        amount = max(get_balance_free(coin), get_balance_frozen(coin))
        if amount <= 0:
            continue

        symbol = creat_symbol(coin, args.basecoin)
        klines = exchange.get_klines_1min(symbol, size=1)
        price = klines[-1][closeindex]
        value = price * amount
        total_value += value
        coin['value'] = value

    print(tb(balances))
    print("total value: %s  %s" % (total_value, args.basecoin))
