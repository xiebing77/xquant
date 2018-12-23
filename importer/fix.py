#!/usr/bin/python3
import sys
sys.path.append('../')
import argparse
from datetime import datetime,timedelta
import db.mongodb as md
from setup import *


def fix_middle_kline(database, collection, start_kline, end_kline):
    print(start_kline)
    print(end_kline)
    mid_kline = {
        'open_time': int((start_kline['open_time'] + end_kline['open_time']) / 2),
        'number_of_trades': int((start_kline['number_of_trades'] + end_kline['number_of_trades']) / 2),
        'close_time': int((start_kline['close_time'] + end_kline['close_time']) / 2),
        'open': str((float(start_kline['open']) + float(end_kline['open'])) / 2),
        'high': str((float(start_kline['high']) + float(end_kline['high'])) / 2),
        'low': str((float(start_kline['low']) + float(end_kline['low'])) / 2),
        'close': str((float(start_kline['close']) + float(end_kline['close'])) / 2),
        'volume': str((float(start_kline['volume']) + float(end_kline['volume'])) / 2),
        'quote_asset_volume': str((float(start_kline['quote_asset_volume']) + float(end_kline['quote_asset_volume'])) / 2),
        'taker_buy_base_asset_volume': str((float(start_kline['taker_buy_base_asset_volume']) + float(end_kline['taker_buy_base_asset_volume'])) / 2),
        'taker_buy_quote_asset_volume': str((float(start_kline['taker_buy_quote_asset_volume']) + float(end_kline['taker_buy_quote_asset_volume'])) / 2),
        'ignore': str(int((float(start_kline['ignore']) + float(end_kline['ignore'])) / 2)),
    }
    print(mid_kline)
    database.insert_one(collection, mid_kline)
    return mid_kline


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

    klines = db.find_sort(collection, {"open_time": {
        "$gte": int(start_time.timestamp())*1000,
        "$lt": int(end_time.timestamp())*1000}}, 'open_time', 1)

    i = 0
    miss_count = 0
    print(len(klines))

    period_ms = period * 1000
    for kline in klines:
        rest = kline['open_time'] % period_ms
        if rest:
            print(kline)
            kline['open_time'] -= rest
            kline['close_time'] = kline['open_time'] + period_ms - 1
            print(kline)
            db.update_one(collection, kline['_id'], kline)

        rest = (kline['close_time'] + 1) % period_ms
        if rest:
            print(kline)
            kline['close_time'] = kline['open_time'] + period_ms - 1
            print(kline)
            db.update_one(collection, kline['_id'], kline)

