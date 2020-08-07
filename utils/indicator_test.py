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
        self.digits = 4
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
        ta_rsis = talib.RSI(self.klines_df["close"])
        ta_rsis = [a for a in ta_rsis]

        #print(" X-Lib  rsis:  ", [round(a, 6) for a in py_rsis][-self.display_count:])
        #print("TA-Lib  rsis:  ", [round(a, 6) for a in ta_rsis][-self.display_count:])

        for i in range(-self.display_count, 0):
            #self.assertEqual(py_rsis[i], ta_rsis[i])
            self.assertTrue(abs(py_rsis[i] - ta_rsis[i]) < 0.01)


    def test_ema(self):
        print("")
        period = 55

        pys = ic.py_emas(self.klines, self.closeindex, period)
        tas = talib.EMA(self.klines_df["close"], period)
        tas = [a for a in tas]

        #print(" X-Lib  emas:  ", [round(a, 6) for a in pys][-self.display_count:])
        #print("TA-Lib  emas:  ", [round(a, 6) for a in tas][-self.display_count:])

        for i in range(-self.display_count, 0):
            #self.assertEqual(pys[i], tas[i])
            self.assertTrue(abs(pys[i] - tas[i]) < 0.01)


    def test_bias(self):
        print("")
        period_s = 21
        period_l = 55

        semas = ic.py_emas(self.klines, self.closeindex, period_s)
        lemas = ic.py_emas(self.klines, self.closeindex, period_l)

        biases = ic.py_biases(semas, lemas)

        print(" X-Lib       semas(%d):  %s" % (period_s, [round(a, self.digits) for a in semas][-self.display_count:]))
        print(" X-Lib       lemas(%d):  %s" % (period_l, [round(a, self.digits) for a in lemas][-self.display_count:]))
        print(" X-Lib  biases(%d, %d):  %s" % (period_s, period_l, [round(a, 4) for a in biases][-self.display_count:]))


    def test_nbias(self):
        print("")
        period = 55

        closes = [float(k[self.closeindex]) for k in self.klines]
        emas = ic.py_emas(self.klines, self.closeindex, period)

        nbiases = ic.py_biases(closes, emas)

        print(" X-Lib      closes:  ", [round(a, self.digits) for a in closes][-self.display_count:])
        print(" X-Lib    emas(%d):  %s" % (period, [round(a, self.digits) for a in emas][-self.display_count:]))
        print(" X-Lib nbiases(%d):  %s" % (period, [round(a, 4) for a in nbiases][-self.display_count:]))


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
