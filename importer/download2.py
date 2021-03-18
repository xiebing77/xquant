#!/usr/bin/python3
import sys
sys.path.append('../')
import argparse
import time
from datetime import datetime, timedelta
import db.mongodb as md
import common.xquant as xq
import common.kline as kl
from exchange.exchange import create_exchange
from db.mongodb import get_mongodb
from setup import *
import pandas as pd
from importer import add_common_arguments, split_time_range


def download_from_exchange(exchange, db, symbol, kline_type, time_range):
    print('%12s %6s   ' % (' ', kline_type), end = '' )
    collection = kl.get_kline_collection(symbol, kline_type)
    open_time_key = exchange.kline_key_open_time
    db.ensure_index(collection, [(open_time_key,1)], unique=True)

    interval = kl.get_interval_timedelta(kline_type)
    if time_range:
        start_time, end_time = split_time_range(time_range)
    else:
        # 续接db中最后一条记录，至今天之前
        klines = db.find_sort(collection, {}, open_time_key, -1, 1)
        if len(klines) > 0:
            start_time = (datetime.fromtimestamp(klines[0][open_time_key]/1000) + interval)
        else:
            start_time = exchange.start_time
        end_time = datetime.now()

    #print(kl.get_open_time(kline_type, end_time))
    """
    if start_time.hour != exchange.start_time.hour:
        print("open time(%s) hour error! %s open time hour: %s" % (start_time, exchange.name, exchange.start_time.hour))
        exit(1)

    if end_time.hour < exchange.start_time.hour:
        end_time -= timedelta(days=1)
    end_time = end_time.replace(hour=exchange.start_time.hour, minute=0, second=0, microsecond=0)
    """

    end_time = end_time.replace(minute=0, second=0, microsecond=0)
    end_time = kl.get_open_time(kline_type, end_time)
    print("time range:  %s ~ %s " % (start_time, end_time))

    size = 1000
    tmp_time = start_time
    while tmp_time < end_time:
        size_interval = size * interval
        if (tmp_time + size_interval) > end_time:
            batch = int((end_time - tmp_time)/interval)
        else:
            batch = size
         # print(batch)

        if batch == 0:
            break

        klines = exchange.get_klines(symbol, kline_type, size=batch, since=1000*int(tmp_time.timestamp()))
        klines_df = pd.DataFrame(klines, columns=exchange.kline_column_names)
        klen = len(klines)
        print(" %20s start time:  %s   %s" % (' ', tmp_time, klen))
        for i in range(klen-1, -1, -1):
            last_open_time = datetime.fromtimestamp(klines_df[open_time_key].values[i]/1000)
            if last_open_time + interval <= end_time:
                break
            klines_df = klines_df.drop([i])
            # last_kline = klines[i]
            # print("%s  %s" % (datetime.fromtimestamp(last_kline[0]/1000),last_kline))
        db_datalines = klines_df.to_dict('records')
        if len(db_datalines) == 0:
            break
        if not db.insert_many(collection, db_datalines):
            for item in db_datalines:
                db.insert_one(collection, item)

        last_time = datetime.fromtimestamp(klines_df[open_time_key].values[-1]/1000) + interval
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

    print("%s connecting..." % (args.m), end='')
    exchange = create_exchange(args.m)
    if not exchange:
        print("market data source error!")
        exit(1)
    print('ok!')

    db = get_mongodb(args.m)

    symbols = args.ss.split(',')
    kline_types = args.kts.split(',')
    for symbol in symbols:
        print('%12s   ' % (symbol))
        for kline_type in kline_types:
            download_from_exchange(exchange, db, symbol, kline_type, args.r)

