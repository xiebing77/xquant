#!/usr/bin/python
import sys
sys.path.append('../')

from datetime import datetime
import unittest

from md.dbmd import DBMD
import utils.indicator as ic
import pandas as pd
import talib

class TestIndicator(unittest.TestCase):

    def setUp(self):
        self.md = DBMD("binance")
        self.md.tick_time = datetime(2020, 8, 1, 8)

        self.display_count = 14
        self.klines = self.md.get_klines("eth_usdt", "1d", 150 + self.display_count)

        self.klines_df = pd.DataFrame(self.klines, columns=self.md.get_kline_column_names())

        for index, value in enumerate(self.md.get_kline_column_names()):
            if value == "close":
                self.closeindex = index
                break


    def tearDown(self):
        pass


    def test_rsi(self):
        py_rsis = ic.py_rsis(self.klines, self.closeindex)
        py_rsis = [round(a, 3) for a in py_rsis][-self.display_count:]
        print(" X-Lib  rsis:  ", py_rsis)

        ta_rsis = talib.RSI(self.klines_df["close"])
        ta_rsis = [round(a, 3) for a in ta_rsis][-self.display_count:]
        print("TA-Lib  rsis:  ", ta_rsis)

        for i in range(self.display_count):
            #self.assertEqual(py_rsis[i], ta_rsis[i])
            self.assertTrue((py_rsis[i] - ta_rsis[i]) < 0.01)


if __name__ == '__main__':
    unittest.main()
