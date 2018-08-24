#!/usr/bin/python3
import sys
sys.path.append('../')
import argparse
from datetime import datetime,timedelta
import db.mongodb as md
from setup import *
from exchange.binanceExchange import BinanceExchange
import pandas as pd

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='klines print or check')
    parser.add_argument('-s', help='symbol (btc_usdt)')
    parser.add_argument('-r', help='time range (2018-7-1,2018-8-1)')
    parser.add_argument('-k', help='kline type (1min、1day...)')

    args = parser.parse_args()
    # print(args)

    if not (args.s and args.r and args.k):
        parser.print_help()
        exit(1)

    time_range = args.r.split(",")
    start_time = datetime.strptime(time_range[0], "%Y-%m-%d")
    end_time = datetime.strptime(time_range[1], "%Y-%m-%d")

    if args.k == "1min":
        collection = "kline_%s" % args.s
        tick_time = start_time
        td = timedelta(minutes=1)
    elif args.k == "1day":
        collection = "kline_1day_%s" % args.s
        tick_time = start_time + timedelta(hours=8)
        td = timedelta(days=1)
    else:
        exit(1)

    exchange = BinanceExchange(debug=True)
    db = md.MongoDB(mongo_user, mongo_pwd, db_name, db_url)
    klines = db.find(collection,{"open_time": {
        "$gte":int(start_time.timestamp())*1000,
        "$lt": int(end_time.timestamp())*1000}})

    i = 0
    miss_start = None
    miss_count = 0

    while tick_time < end_time:
        ts = int(tick_time.timestamp()*1000)
        #print(ts, " ~ ", klines[i]["open_time"])
        if ts == klines[i]["open_time"]:
            #print(tick_time, " match  ok")
            i += 1
        else:
            #print(ts, " ~ ", klines[i]["open_time"])
            kline = db.find(collection, {"open_time": ts})
            if kline:
                if not miss_start:
                    print("有乱序")
                    break
            else:
                miss_count += 1
                if not miss_start:
                    miss_start = ts

                if ts > klines[i]["open_time"]:
                    print(ts, " ~ ", klines[i]["open_time"], " ~ ", i, " ~ ", datetime.fromtimestamp(klines[i]["open_time"]/1000))
                    i += 1

        tick_time += td

    if not miss_start:
        exit(1)

    print("miss start: %s, count: %d " % (miss_start, miss_count))

    if args.k == "1min":
        interval = 60 * 1000
        klines = exchange.get_klines_1min(args.s, size=miss_count, since=miss_start)
    elif args.k == "1day":
        interval = 24 * 60 * 60 * 1000
        klines = exchange.get_klines_1day(args.s, size=miss_count, since=miss_starts)

    klines_df = pd.DataFrame(klines, exchange.get_kline_column_names())

    records = klines_df.to_dict('records')
    tmp_ts = miss_start
    for record in records:
        if record["open_time"] != tmp_ts:
            print("从交易所获取的k线不符合预期")
            print("tmp_ts: %d  miss" % tmp_ts)
            print(klines_df)
            exit(1)
        tmp_ts += interval

    db.insert_many(collection, records)
    print("补齐了一段缺失数据，请重复执行")


