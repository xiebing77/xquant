#!/usr/bin/python3
import sys
sys.path.append('../')
import argparse
from datetime import datetime,timedelta
import db.mongodb as md
from setup import *
# import pandas as pd

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

    db = md.MongoDB(mongo_user, mongo_pwd, db_name, db_url)
    klines = db.find(collection,{"open_time": {
        "$gte":int(start_time.timestamp())*1000,
        "$lt": int(end_time.timestamp())*1000}})

    i = 0
    while tick_time < end_time:
        ts = int(tick_time.timestamp()*1000)
        #print(ts, " ~ ", klines[i]["open_time"])
        if ts ==klines[i]["open_time"]:
            print(tick_time, " match  ok")
        else:
            kline = db.find(collection, {"open_time": ts})
            if kline:
                print(tick_time, " find ok")
            else:
                print(tick_time, " find  miss")

        tick_time += td
        i += 1
