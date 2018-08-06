#!/usr/bin/python3
import argparse
import time
import db.mongodb as md
from common.xquant import creat_symbol
from exchange.binanceExchange import BinanceExchange
from setup import *

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Binance Importer')
    parser.add_argument('-b', help='base coin')
    parser.add_argument('-t', help='target coin')
    parser.add_argument('-s', help='start time (2018-8-1)')
    parser.add_argument('-e', help='end time (2018-9-1)')

    args = parser.parse_args()
    # print(args)
    if not (args.b and args.t and args.s and args.e):
        parser.print_help()
        exit(1)

    base_coin = args.b
    target_coin = args.t
    start_time = time.mktime(time.strptime(args.s, "%Y-%m-%d"))
    end_time = time.mktime(time.strptime(args.e, "%Y-%m-%d"))
    print(start_time)
    print(end_time)

    db = md.MongoDB(mongo_user, mongo_pwd, db_name, db_url)
    exchange = BinanceExchange(debug=True)
    symbol = creat_symbol(base_coin, target_coin)
    size = 500
    tmp_time = start_time

    while tmp_time < end_time:

        kline = exchange.get_klines_1min(symbol, size=size, since=tmp_time)

