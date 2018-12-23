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
    print("range: [%s, %s)"%(start_time, end_time))

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

    klines = db.find_sort(collection, {"open_time": {
        "$gte": int(start_time.timestamp())*1000,
        "$lt": int(end_time.timestamp())*1000}}, 'open_time', 1)
    klines_len = len(klines)
    print("klines len: %d"% klines_len)

    i = 0
    repeat_count = 0
    wrong_count = 0
    miss_count = 0
    while tick_time < end_time:
        if i >= klines_len:
            miss_count += (end_time - tick_time).total_seconds()/td.total_seconds()
            print("miss tail  %s~%s" % (tick_time, end_time) )
            break

        next_tick_time = tick_time + td
        open_time = klines[i]["open_time"]/1000
        #print("tick_time   %s, next_tick_time %s" % (tick_time, next_tick_time) )
        #print("tick_time   %s, open_time %s" % (tick_time.timestamp(), open_time) )

        if open_time < tick_time.timestamp():
            i += 1
            repeat_count += 1
            print("repeat %s" % (datetime.fromtimestamp(open_time)))
        elif open_time == tick_time.timestamp():
            i += 1
            tick_time = next_tick_time
        elif open_time < next_tick_time.timestamp():
            i += 1
            tick_time = next_tick_time
            wrong_count += 1
            print("tick_time %s, wrong 2 %s" % (tick_time, datetime.fromtimestamp(open_time)))
        else:
            miss_count += 1
            print("miss   %s" % (tick_time) )
            tick_time = next_tick_time

    print("repeat count: ", repeat_count)
    print("wrong  count: ", wrong_count)
    print("miss   count: ", miss_count)
