#!/usr/bin/python3
import sys
sys.path.append('../')
from datetime import datetime, timedelta
import db.mongodb as md
from setup import *
import common.xquant as xq
from importer import add_common_arguments, split_time_range

if __name__ == "__main__":
    parser = add_common_arguments('check kline')
    args = parser.parse_args()
    # print(args)

    if not (args.s and args.r and args.k and args.m):
        parser.print_help()
        exit(1)

    start_time, end_time = split_time_range(args.r)
    print("range: [%s, %s)"%(start_time, end_time))

    interval = args.k
    collection = xq.get_kline_collection(args.s, interval)
    td = xq.get_interval_timedelta(interval)
    period = xq.get_interval_seconds(interval)
    tick_time = xq.get_open_time(interval, start_time)
    if tick_time < start_time:
        tick_time = xq.get_open_time(interval, start_time+td)


    db = md.MongoDB(mongo_user, mongo_pwd, args.m, db_url)
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
            kline = klines[i]
            if args.display:
                open_time = datetime.fromtimestamp(int(kline["open_time"])/1000)
                close_time = datetime.fromtimestamp(int(kline["close_time"])/1000)
                print("(%s ~ %s)  high: %s  low: %s  close: %s  volume: %s" %
                    (open_time, close_time, kline["high"], kline["low"], kline["close"], kline["volume"]))
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
