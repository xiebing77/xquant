#!/usr/bin/python3
import sys
sys.path.append('../')
import argparse
import common.kline as kl
from exchange.exchange import create_exchange, exchange_names, BINANCE_SPOT_EXCHANGE_NAME
from tabulate import tabulate as tb
import pprint

from common.xquant import creat_symbol, get_balance_coin, get_balance_free, get_balance_frozen


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='account infomation')
    parser.add_argument('-exchange', default=BINANCE_SPOT_EXCHANGE_NAME, choices=exchange_names, help='exchange name')
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
    #print(tb(balances))

    if exchange.kline_data_type == kl.KLINE_DATA_TYPE_LIST:
        closeseat = exchange.kline_idx_close
    else:
        closeseat = exchange.kline_key_close

    total_value = 0
    for item in balances:
        amount = max(get_balance_free(item), get_balance_frozen(item))
        if amount < 0:
            continue

        coin = get_balance_coin(item)
        if coin.upper() == args.basecoin.upper():
            value = amount
        else:
            #print(coin)
            symbol = creat_symbol(coin, args.basecoin)
            klines = exchange.get_klines_1min(symbol, size=1)
            price = float(klines[-1][closeseat])
            value = price * amount

        total_value += value
        item['value'] = value

    print(tb(balances))
    print("total value: %s  %s" % (total_value, args.basecoin))
