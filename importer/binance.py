#!/usr/bin/python3
import sys
sys.path.append('../')
import argparse
import time
from datetime import datetime
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
    parser.add_argument('-k', help='kline type (1min、1day...)')

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


    if args.k == "1min":
        interval = 60 * 1000
        collection = "kline_%s" % symbol
    elif args.k == "1day":
        interval = 24 * 60 * 60 * 1000
        collection = "kline_1day_%s" % symbol
    else:
        exit(1)


    print("collection: ", collection)
    size = 1000
    tmp_time = start_time

    while tmp_time < end_time:
        print(datetime.fromtimestamp(tmp_time/1000))
        if (tmp_time + size * interval) > end_time:
            batch = int((end_time - tmp_time)/interval)
        else:
            batch = size
         # print(batch)
        if args.k == "1min":
            klines = exchange.get_klines_1min(symbol, size=batch, since=tmp_time)
        elif args.k == "1day":
            klines = exchange.get_klines_1day(symbol, size=batch, since=tmp_time)

        #klen = len(klines)
        #print("klines len: ", klen)
        #print(klines)
        #print("klines[0]: ", klines.ix[0])
        #print("klines[-1]: ", klines.ix[klen-1])
        #print("records: ", klines.to_dict('records'))
        db.insert_many(collection, klines.to_dict('records'))
        tmp_time += batch * interval

    # df = db.get_kline(no_id=False)
    # pd.set_option('display.max_columns', None)
    # pd.set_option('display.max_rows', None)
    # pd.set_option('display.max_colwidth', -1)
    # print(df)
