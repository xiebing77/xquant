#!/usr/bin/python3
import sys
sys.path.append('../')
import time
from datetime import datetime, timedelta
import db.mongodb as md
import common.xquant as xq
import common.kline as kl
import exchange as ex
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

    db = md.MongoDB(mongo_user, mongo_pwd, args.m, db_url)
    db.ensure_index(collection, [("open_time",1)], unique=True)

    exchange = ex.create_exchange(args.m)
    if not exchange:
        print("market data source error!")
        exit(1)
    exchange.connect()

    # 注意，下面代码有隐患，在上午8点前取1d、12h时，最后的一个是不完整的，后续再整改
    if args.r:
        start_time, end_time = split_time_range(args.r)
    else:
        # 续接db中最后一条记录，至今天之前
        klines = db.find_sort(collection, {}, 'open_time', -1, 1)
        if len(klines) > 0:
            start_time = (exchange.get_time_from_data_ts(klines[0]["open_time"]) + interval).replace(hour=0,minute=0,second=0,microsecond=0)
        else:
            start_time = None
        end_time = datetime.now().replace(hour=0,minute=0,second=0,microsecond=0)

    if not start_time:
        start_time = exchange.start_time

    size = 1000
    tmp_time = start_time

    while tmp_time < end_time:
        print(tmp_time, end="    ")
        if (tmp_time + size * interval) > end_time:
            batch = int((end_time - tmp_time)/interval)
        else:
            batch = size
         # print(batch)

        klines = exchange.get_klines(symbol, args.k, size=batch, since=exchange.get_data_ts_from_time(tmp_time))

        klines_df = pd.DataFrame(klines, columns=exchange.get_kline_column_names())

        klen = len(klines)
        print("klines len: ", klen)
        #print(klines)
        #print("klines[0]: ", klines.ix[0])
        #print("klines[-1]: ", klines.ix[klen-1])
        #print("records: ", klines.to_dict('records'))
        if not db.insert_many(collection, klines_df.to_dict('records')):
            for item in klines_df.to_dict('records'):
                db.insert_one(collection, item)
        tmp_time += batch * interval

    # df = db.get_kline(no_id=False)
    # pd.set_option('display.max_columns', None)
    # pd.set_option('display.max_rows', None)
    # pd.set_option('display.max_colwidth', -1)
    # print(df)
