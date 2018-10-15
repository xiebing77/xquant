#!/usr/bin/python3
import sys
sys.path.append('../')
import argparse
from datetime import datetime, timedelta
import db.mongodb as md
from setup import *
import common.xquant as xq

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='klines print or check')
    parser.add_argument('-s', help='symbol (btc_usdt)')
    parser.add_argument('-r', help='time range (2018-7-1,2018-8-1)')
    parser.add_argument('-k', help='kline type (1m、4h、1d...)')

    args = parser.parse_args()
    # print(args)

    if not (args.s and args.r and args.k):
        parser.print_help()
        exit(1)

    time_range = args.r.split(",")
    start_time = datetime.strptime(time_range[0], "%Y-%m-%d")
    end_time = datetime.strptime(time_range[1], "%Y-%m-%d")

    interval = args.k
    collection = xq.get_kline_collection(args.s, interval)
    td = xq.get_interval_timedelta(interval)
    period = xq.get_interval_seconds(interval)
    tick_time = xq.get_open_time(interval, start_time)
    if tick_time < start_time:
        tick_time = xq.get_open_time(interval, start_time+td)



    db = md.MongoDB(mongo_user, mongo_pwd, db_name, db_url)
    target_len = int((int(end_time.timestamp()) - int(start_time.timestamp())) / period)
    print("Target length:", target_len)

    length = db.count(collection, {"open_time": {
        "$gte": int(start_time.timestamp())*1000,
        "$lt": int(end_time.timestamp())*1000}})

    print("Real length:", length)
    # if length == target_len:
    #     print('No data lost. Everything is okay.')
    #     exit(0)

    klines = db.find_sort(collection, {"open_time": {
        "$gte": int(start_time.timestamp())*1000,
        "$lt": int(end_time.timestamp())*1000}}, 'open_time', 1)

    i = 0
    miss_start = None
    miss_count = target_len - length
    if miss_count != 0:
        print("miss count: %d " % miss_count)
        exit(1)

    # scan all klines to check integration
    while i < len(klines):
        ts = int(tick_time.timestamp()*1000)
        if ts == klines[i]["open_time"]:
            i += 1
        else:
            miss_start = ts
            break

        tick_time += td

    if miss_start:
        miss_start = int(tick_time.timestamp()*1000)
        print('Some kline data is not correct. Please check below information', miss_start)
        print(klines[i])



