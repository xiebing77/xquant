#!/usr/bin/python3
import sys
sys.path.append('../')
import argparse
import time
from datetime import datetime
import db.mongodb as md
import common.xquant as xq
from exchange.binanceExchange import BinanceExchange
from setup import *
import pandas as pd

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Binance Importer')
    parser.add_argument('-b', help='base coin')
    parser.add_argument('-t', help='target coin')
    parser.add_argument('-s', help='start time (2018-8-1)')
    parser.add_argument('-e', help='end time (2018-9-1)')
    parser.add_argument('-k', help='kline type (1m、4h、1d...)')

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
    symbol = xq.creat_symbol(base_coin=base_coin, target_coin=target_coin)

    interval = 1000 * xq.get_interval_seconds(args.k)

    collection = xq.get_kline_collection(symbol, args.k)
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

        klines = exchange.get_klines(symbol, args.k, size=batch, since=tmp_time)

        klines_df = pd.DataFrame(klines, columns=exchange.get_kline_column_names())

        klen = len(klines)
        print("klines len: ", klen)
        #print(klines)
        #print("klines[0]: ", klines.ix[0])
        #print("klines[-1]: ", klines.ix[klen-1])
        #print("records: ", klines.to_dict('records'))
        if not db.insert_many(collection, klines_df.to_dict('records')):
            for item in klines_df.to_dict('records'):
                db.insert_one(collection, item)
        tmp_time += batch * interval

    # df = db.get_kline(no_id=False)
    # pd.set_option('display.max_columns', None)
    # pd.set_option('display.max_rows', None)
    # pd.set_option('display.max_colwidth', -1)
    # print(df)
