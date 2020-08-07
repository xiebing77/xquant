#!/usr/bin/python
import sys
sys.path.append('../')

from datetime import datetime
import unittest
import pandas as pd
import talib

from md.dbmd import DBMD
import utils.indicator as ic
import common.xquant as xq

class TestIndicator(unittest.TestCase):

    def setUp(self):
        self.symbol = "eth_usdt"
        self.interval = xq.KLINE_INTERVAL_1DAY
        self.display_count = 14

        self.md = DBMD("binance")
        self.md.tick_time = datetime(2018, 1, 1, 8)

        self.klines = self.md.get_klines(self.symbol, self.interval, 150 + self.display_count)

        self.klines_df = pd.DataFrame(self.klines, columns=self.md.get_kline_column_names())

        for index, value in enumerate(self.md.get_kline_column_names()):
            if value == "close":
                self.closeindex = index
                break

        self.count = 1000
        self.steps = 1
        self.td = xq.get_interval_timedelta(xq.KLINE_INTERVAL_1MINUTE) * self.steps


    def tearDown(self):
        pass


    def test_rsi(self):
        print("")
        py_rsis = ic.py_rsis(self.klines, self.closeindex)
        py_rsis = [round(a, 3) for a in py_rsis][-self.display_count:]
        print(" X-Lib  rsis:  ", py_rsis)

        ta_rsis = talib.RSI(self.klines_df["close"])
        ta_rsis = [round(a, 3) for a in ta_rsis][-self.display_count:]
        print("TA-Lib  rsis:  ", ta_rsis)

        for i in range(self.display_count):
            #self.assertEqual(py_rsis[i], ta_rsis[i])
            self.assertTrue(abs(py_rsis[i] - ta_rsis[i]) < 0.01)

    def test_ema(self):
        print("")
        period = 55
        pys = ic.py_emas(self.klines, self.closeindex, period)
        pys = [round(a, 3) for a in pys][-self.display_count:]
        print(" X-Lib  emas:  ", pys)

        tas = talib.EMA(self.klines_df["close"], period)
        tas = [round(a, 3) for a in tas][-self.display_count:]
        print("TA-Lib  emas:  ", tas)

        for i in range(self.display_count):
            #self.assertEqual(pys[i], tas[i])
            self.assertTrue(abs(pys[i] - tas[i]) < 0.01)

    def _test_perf_xlib_rsi(self):
        for i in range(self.count):
            klines = self.md.get_klines(self.symbol, self.interval, 150 + self.display_count)

            py_rsis = ic.py_rsis(klines, self.closeindex)
            py_rsis = [round(a, 3) for a in py_rsis][-self.display_count:]

            self.md.tick_time += self.td

    def _test_perf_talib_rsi(self):
        for i in range(self.count):
            klines = self.md.get_klines(self.symbol, self.interval, 150 + self.display_count)
            klines_df = pd.DataFrame(klines, columns=self.md.get_kline_column_names())

            ta_rsis = talib.RSI(klines_df["close"])
            ta_rsis = [round(a, 3) for a in ta_rsis][-self.display_count:]

            self.md.tick_time += self.td

if __name__ == '__main__':
    unittest.main()
