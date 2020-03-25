#!/usr/bin/python3
import sys
sys.path.append('../')
import argparse
import time
from datetime import datetime, timedelta
import db.mongodb as md
import common.xquant as xq
from exchange.binanceExchange import BinanceExchange
from setup import *
import pandas as pd
from importer import add_common_arguments, split_time_range


def download_from_exchange(exchange, db, symbol, kline_type, time_range):
    print('%10s %4s      ' % (symbol, kline_type), end = '' )
    collection = xq.get_kline_collection(symbol, kline_type)
    db.ensure_index(collection, [("open_time",1)], unique=True)

    interval = timedelta(seconds=xq.get_interval_seconds(kline_type))
    if time_range:
        start_time, end_time = split_time_range(time_range)
    else:
        # 续接db中最后一条记录，至今天之前
        klines = db.find_sort(collection, {}, 'open_time', -1, 1)
        if len(klines) > 0:
            start_time = (datetime.fromtimestamp(klines[0]["open_time"]/1000) + interval)
        else:
            start_time = exchange.start_time
        end_time = datetime.now()


    if start_time.hour != exchange.start_time.hour:
        print("open time(%s) hour error! %s open time hour: %s" % (start_time, exchange.name, exchange.start_time.hour))
        exit(1)

    if end_time.hour < exchange.start_time.hour:
        end_time -= timedelta(days=1)
    end_time = end_time.replace(hour=exchange.start_time.hour, minute=0, second=0, microsecond=0)
    print("time range:  %s ~ %s " % (start_time, end_time))

    size = 1000
    tmp_time = start_time
    while tmp_time < end_time:
        print(tmp_time, end="    ")

        size_interval = size * interval
        if (tmp_time + size_interval) > end_time:
            batch = int((end_time - tmp_time)/interval)
        else:
            batch = size
         # print(batch)

        klines = exchange.get_klines(symbol, kline_type, size=batch, since=1000*int(tmp_time.timestamp()))
        klines_df = pd.DataFrame(klines, columns=exchange.get_kline_column_names())
        klen = len(klines)
        print("klines len: ", klen)
        for i in range(klen-1, -1, -1):
            last_open_time = datetime.fromtimestamp(klines_df["open_time"].values[i]/1000)
            if last_open_time + interval <= end_time:
                break
            klines_df = klines_df.drop([i])
            # last_kline = klines[i]
            # print("%s  %s" % (datetime.fromtimestamp(last_kline[0]/1000),last_kline))

        if not db.insert_many(collection, klines_df.to_dict('records')):
            for item in klines_df.to_dict('records'):
                db.insert_one(collection, item)

        last_time = datetime.fromtimestamp(klines_df["open_time"].values[-1]/1000) + interval
        if last_time > tmp_time + batch * interval:
            batch = int((last_time - tmp_time)/interval)
        tmp_time += batch * interval


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='klines print or check')
    parser.add_argument('-m', help='market data source')
    parser.add_argument('-r', help='time range (2018-7-1T8' + xq.time_range_split + '2018-8-1T8)')
    parser.add_argument('-ss', help='symbols: btc_usdt,eth_usdt')
    parser.add_argument('-kts', help='kline types: 1m,4h,1d')
    args = parser.parse_args()
    print(args)
    if not (args.ss and args.kts and args.m):
        parser.print_help()
        exit(1)

    if args.m == "binance":
        print("%s connecting......" % args.m)
        exchange = BinanceExchange(debug=True)
        print("%s connect ok" % args.m)
    else:
        print("market data source error!")
        exit(1)

    db = md.MongoDB(mongo_user, mongo_pwd, args.m, db_url)

    symbols = args.ss.split(',')
    kline_types = args.kts.split(',')
    for symbol in symbols:
        for kline_type in kline_types:
            download_from_exchange(exchange, db, symbol, kline_type, args.r)

