#!/usr/bin/python3
import argparse
import time
import db.mongodb as md
from common.xquant import creat_symbol
from exchange.binanceExchange import BinanceExchange
from setup import *
# import pandas as pd

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
    start_time = int(time.mktime(time.strptime(args.s, "%Y-%m-%d"))) * 1000
    end_time = int(time.mktime(time.strptime(args.e, "%Y-%m-%d"))) * 1000
    print("start time:", start_time, args.s)
    print("end time:", end_time, args.e)

    db = md.MongoDB(mongo_user, mongo_pwd, db_name, db_url)
    exchange = BinanceExchange(debug=True)
    symbol = creat_symbol(base_coin=base_coin, target_coin=target_coin)
    size = 1000
    interval = 60 * 1000
    tmp_time = start_time

    while tmp_time < end_time:
        if (tmp_time + size * interval) > end_time:
            batch = int((end_time - tmp_time)/interval)
        else:
            batch = size
        # print(batch)
        kline = exchange.get_klines_1min(symbol, size=batch, since=tmp_time)
        db.insert_kline(symbol, kline)
        tmp_time += batch * interval

    # df = db.get_kline(no_id=False)
    # pd.set_option('display.max_columns', None)
    # pd.set_option('display.max_rows', None)
    # pd.set_option('display.max_colwidth', -1)
    # print(df)
