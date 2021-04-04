#!/usr/bin/python
import sys
sys.path.append('../')

from datetime import datetime
import unittest
from pprint import pprint

import numpy as np
import pandas as pd
import talib
import utils.ti as ti

import common.xquant as xq
import common.kline as kl
from md.dbmd import DBMD

class TestDBMD(unittest.TestCase):
    symbol = "eth_usdt"
    digits = 4

    interval = kl.KLINE_INTERVAL_1DAY
    interval_td = kl.get_interval_timedelta(interval)
    pre_count = 150
    display_count = 10

    tick_interval = kl.KLINE_INTERVAL_1MINUTE
    tick_collection = kl.get_kline_collection(symbol, tick_interval)
    tick_td = kl.get_interval_timedelta(tick_interval)

    start_time = datetime(2017, 9, 1)
    end_time = datetime(2020, 8, 1)
    md = DBMD("binance")

    def setUp(self):
        self.md.tick_time = self.start_time
        tick = (self.end_time - self.start_time) / self.tick_td
        print("tick td=%s, tick=%d, time rang: %s ~ %s" % (self.tick_td, tick, self.start_time, self.end_time))

    def tearDown(self):
        pass

    def perf_get_json_klines(self):
        while self.md.tick_time < self.end_time:
            klines = self.md.get_json_klines(self.symbol, self.interval, self.pre_count + self.display_count)
            self.md.tick_time += self.tick_td

    def perf_get_klines(self):
        while self.md.tick_time < self.end_time:
            klines = self.md.get_klines(self.symbol, self.interval, self.pre_count + self.display_count)
            self.md.tick_time += self.tick_td


    def perf_get_klines_adv(self):
        total_interval_count = int((self.end_time - self.start_time) / self.interval_td) + self.pre_count
        print("total_interval_count: %s" % (total_interval_count))
        interval_collection = kl.get_kline_collection(self.symbol, self.interval)
        interval_klines = self.md.get_original_klines(interval_collection, self.start_time - self.interval_td * self.pre_count, self.end_time)
        kl = interval_klines[0]
        kl_key_open_time = self.md.open_time_key
        print("open_time: %s" % (self.md.get_time_from_data_ts(kl[kl_key_open_time])))
        #print("json:  %s" % (kl))

        ti.EMA(interval_klines, "close", 13)
        ti.EMA(interval_klines, "close", 21)
        ti.EMA(interval_klines, "close", 55)
        ti.BIAS_EMA(interval_klines, 13, 21)
        ti.BIAS_EMA(interval_klines, 21, 55)
        ti.RSI(interval_klines, "close")
        #print(interval_klines[self.pre_count:self.pre_count+2])
        #print(interval_klines[-2:])
        #pprint(interval_klines[self.pre_count])
        #pprint(interval_klines[-1])

        for i in range(self.pre_count+1):
            if self.md.get_time_from_data_ts(interval_klines[i][kl_key_open_time]) >= self.start_time:
                break
        interval_idx = i
        kl = interval_klines[interval_idx]
        print("interval_idx: %s" % (interval_idx))
        print("open time: %s" % (self.md.get_time_from_data_ts(kl[kl_key_open_time])))
        #print("json:  %s" % (kl))

        for i in range(interval_idx, len(interval_klines)):
            start_i = i - self.pre_count
            if start_i < 0:
                start_i = 0
            history_kls = interval_klines[start_i:i]
            #print(len(history_kls))

            interval_open_ts = interval_klines[i][kl_key_open_time]
            interval_open_time = self.md.get_time_from_data_ts(interval_open_ts)
            #print(interval_open_time)

            tick_klines = self.md.get_original_klines(self.tick_collection, interval_open_time, interval_open_time+self.interval_td)
            new_interval_kl = tick_klines[0]
            for tick_kl in tick_klines[1:]:
                tick_open_time = self.md.get_time_from_data_ts(tick_kl[kl_key_open_time])
                #print(tick_open_time)
                new_interval_kl["close"] = tick_kl["close"]
                new_interval_kl["close_time"] = tick_kl["close_time"]

                if new_interval_kl["high"] < tick_kl["high"]:
                    new_interval_kl["high"] = tick_kl["high"]
                if new_interval_kl["low"] > tick_kl["low"]:
                    new_interval_kl["low"] = tick_kl["low"]

                cur_kls = history_kls + [new_interval_kl]
                ti.EMA(cur_kls, "close", 13)
                ti.EMA(cur_kls, "close", 21)
                ti.EMA(cur_kls, "close", 55)
                ti.BIAS_EMA(cur_kls, 13, 21)
                ti.BIAS_EMA(cur_kls, 21, 55)
                ti.RSI(cur_kls, "close")
                #pprint(cur_kls[-2])
                #pprint(cur_kls[-1])
                #return



if __name__ == '__main__':
    unittest.main()
