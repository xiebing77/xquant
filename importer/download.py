#!/usr/bin/python3
import sys
sys.path.append('../')
import time
from datetime import datetime, timedelta
import db.mongodb as md
import common.xquant as xq
from exchange.binanceExchange import BinanceExchange
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
    interval = timedelta(seconds=xq.get_interval_seconds(args.k))

    collection = xq.get_kline_collection(symbol, args.k)
    #print("collection: ", collection)

    db = md.MongoDB(mongo_user, mongo_pwd, args.m, db_url)
    db.ensure_index(collection, [("open_time",1)], unique=True)

    if args.r:
        start_time, end_time = split_time_range(args.r)
    else:
        # 续接db中最后一条记录，至今天之前
        klines = db.find_sort(collection, {}, 'open_time', -1, 1)
        if len(klines) > 0:
            start_time = (datetime.fromtimestamp(klines[0]["open_time"]/1000) + interval)
        else:
            start_time = None
        end_time = datetime.now()

    if args.m == "binance":
        open_hour = BinanceExchange.start_time.hour
        exchange = BinanceExchange(debug=True)
        if not start_time:
            start_time = BinanceExchange.start_time
    else:
        print("market data source error!")
        exit(1)

    if start_time.hour != open_hour:
        print("open time hour error! %s open time hour: %s" % (args.m, open_hour))
        exit(1)

    if end_time.hour < open_hour:
        end_time -= timedelta(days=1)
    end_time.replace(hour=open_hour, minute=0, second=0, microsecond=0)
    print("download time range(%s ~ %s)" % (start_time, end_time))

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

        klines = exchange.get_klines(symbol, args.k, size=batch, since=1000*int(tmp_time.timestamp()))
        klines_df = pd.DataFrame(klines, columns=exchange.get_kline_column_names())
        klen = len(klines)
        print("klines len: ", klen)

        if not db.insert_many(collection, klines_df.to_dict('records')):
            for item in klines_df.to_dict('records'):
                db.insert_one(collection, item)

        last_time = datetime.fromtimestamp(klines_df["open_time"].values[-1]/1000) + interval
        if last_time > tmp_time + batch * interval:
            batch = (last_time - tmp_time)/interval
        tmp_time += batch * interval
