#!/usr/bin/python3
import sys
sys.path.append('../')
import time
from datetime import datetime, timedelta
import common.xquant as xq
import common.kline as kl
from exchange.exchange import create_exchange
from db.mongodb import get_mongodb
from setup import *
import pandas as pd
from importer import add_common_arguments, split_time_range

if __name__ == "__main__":
    parser = add_common_arguments('Binance Importer')
    args = parser.parse_args()
    # print(args)
    if not (args.s and args.k and args.m):
        parser.print_help()
        exit(1)

    symbol = args.s
    interval = timedelta(seconds=kl.get_interval_seconds(args.k))

    collection = kl.get_kline_collection(symbol, args.k)
    #print("collection: ", collection)

    db = get_mongodb(args.m)
    db.ensure_index(collection, [("open_time",1)], unique=True)

    exchange = create_exchange(args.m)
    if not exchange:
        print("market data source error!")
        exit(1)

    if args.r:
        start_time, end_time = split_time_range(args.r)
    else:
        # 续接db中最后一条记录，至今天之前
        klines = db.find_sort(collection, {}, 'open_time', -1, 1)
        if len(klines) > 0:
            start_time = (exchange.get_time_from_data_ts(klines[0]["open_time"]) + interval)
        else:
            start_time = None
        end_time = datetime.now()

    print("%s connecting..." % (args.m), end='')
    exchange.connect()
    print('ok!')

    open_hour = exchange.start_time.hour

    if start_time.hour != open_hour:
        print("open time(%s) hour error! %s open time hour: %s" % (start_time, args.m, open_hour))
        exit(1)

    if end_time.hour < open_hour:
        end_time -= timedelta(days=1)
    end_time = end_time.replace(hour=open_hour, minute=0, second=0, microsecond=0)
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

        klines = exchange.get_klines(symbol, args.k, size=batch, since=exchange.get_data_ts_from_time(tmp_time))
        klines_df = pd.DataFrame(klines, columns=exchange.kline_column_names)
        klen = len(klines)
        print("klines len: ", klen)
        for i in range(klen-1, -1, -1):
            last_open_time = exchange.get_time_from_data_ts(klines_df["open_time"].values[i])
            if last_open_time + interval <= end_time:
                break
            klines_df = klines_df.drop([i])

        if not db.insert_many(collection, klines_df.to_dict('records')):
            for item in klines_df.to_dict('records'):
                db.insert_one(collection, item)

        last_time = exchange.get_time_from_data_ts(klines_df["open_time"].values[-1]) + interval
        if last_time > tmp_time + batch * interval:
            batch = int((last_time - tmp_time)/interval)
        tmp_time += batch * interval
