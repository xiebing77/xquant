#!/usr/bin/python
import sys
sys.path.append('../')

from datetime import datetime
import unittest
import pandas as pd
import talib

from md.dbmd import DBMD
import utils.indicator as ic
import xlib.ti as xti
import common.xquant as xq
import common.kline as kl
import exchange.exchange  as ex

class TestIndicator(unittest.TestCase):

    def setUp(self):
        self.symbol = "eth_usdt"
        self.digits = 4
        self.interval = kl.KLINE_INTERVAL_1DAY
        self.display_count = 10

        exchange_name = ex.BINANCE_SPOT_EXCHANGE_NAME
        self.md = DBMD(exchange_name)
        self.md.tick_time = datetime(2019, 1, 1, 8)

        self.klines = self.md.get_klines(self.symbol, self.interval, 150 + self.display_count)

        self.klines_df = pd.DataFrame(self.klines, columns=self.md.get_kline_column_names())

        self.closeseat = self.md.get_kline_seat_close()
        self.closekey = ex.get_kline_key_close(exchange_name)

        self.count = 5000
        self.steps = 1
        self.td = kl.get_interval_timedelta(kl.KLINE_INTERVAL_1MINUTE) * self.steps


    def tearDown(self):
        pass


    def _test_rsi(self):
        print("")
        py_rsis = ic.py_rsis(self.klines, self.closeseat)
        ta_rsis = talib.RSI(self.klines_df[self.closekey])
        #print(" X-Lib  rsis:  ", [round(a, 6) for a in py_rsis][-self.display_count:])
        #print("TA-Lib  rsis:  ", [round(a, 6) for a in ta_rsis][-self.display_count:])

        for i in range(-self.display_count, 0):
            #self.assertEqual(py_rsis[i], ta_rsis[i])
            self.assertTrue(abs(py_rsis[i] - ta_rsis.values[i]) < 0.01)


    def test_ema(self):
        print("test ema")
        period = 55

        pys = ic.py_emas(self.klines, self.closeseat, period)
        tas = talib.EMA(self.klines_df[self.closekey], period)

        closes = [c for c in pd.to_numeric(self.klines_df[self.closekey])]
        xtis = xti.EMA(closes, period)

        #kl_xtis = xti.EMA_KL(self.klines, self.closeseat, period)

        print("    ic  emas:  ", [round(a, 6) for a in pys][-self.display_count:])
        print("TA-Lib  emas:  ", [round(a, 6) for a in tas][-self.display_count:])
        print(" X-Lib  emas:  ", [round(a, 6) for a in xtis][-self.display_count:])
        #print(" X-Lib kl emas:  ", [round(a, 6) for a in kl_xtis][-self.display_count:])

        for i in range(-self.display_count, 0):
            #self.assertEqual(pys[i], tas[i])
            self.assertTrue(abs(pys[i] - tas.values[i]) < 0.01)
            self.assertTrue(abs(xtis[i] - tas.values[i]) < 0.01)
            #self.assertTrue(abs(kl_xtis[i] - tas.values[i]) < 0.01)


    def _test_bias(self):
        print("")
        period_s = 21
        period_l = 55

        semas = ic.py_emas(self.klines, self.closeseat, period_s)
        ta_semas = talib.EMA(self.klines_df[self.closekey], period_s)
        print(" X-Lib       semas(%d):  %s" % (period_s, [round(a, self.digits) for a in semas][-self.display_count:]))
        print("TA-Lib       semas(%d):  %s" % (period_s, [round(a, self.digits) for a in ta_semas][-self.display_count:]))
        for i in range(-self.display_count, 0):
            self.assertTrue(abs(semas[i] - ta_semas.values[i]) < 0.01)

        lemas = ic.py_emas(self.klines, self.closeseat, period_l)
        ta_lemas = talib.EMA(self.klines_df[self.closekey], period_l)
        print(" X-Lib       lemas(%d):  %s" % (period_l, [round(a, self.digits) for a in lemas][-self.display_count:]))
        print("TA-Lib       lemas(%d):  %s" % (period_l, [round(a, self.digits) for a in ta_lemas][-self.display_count:]))
        for i in range(-self.display_count, 0):
            self.assertTrue(abs(lemas[i] - ta_lemas.values[i]) < 0.01)

        biases = ic.py_biases(semas, lemas)
        ta_biases = ic.pd_biases(ta_semas, ta_lemas)
        print(" X-Lib  biases(%d, %d):  %s" % (period_s, period_l, [round(a, 4) for a in biases][-self.display_count:]))
        print("TA-Lib  biases(%d, %d):  %s" % (period_s, period_l, [round(a, 4) for a in ta_biases][-self.display_count:]))
        for i in range(-self.display_count, 0):
            self.assertTrue(abs(biases[i] - ta_biases.values[i]) < 0.01)



    def _test_nbias(self):
        print("")
        period = 55

        closes = [float(k[self.closeseat]) for k in self.klines]
        print("           closes:  ", [round(a, self.digits) for a in closes][-self.display_count:])

        emas = ic.py_emas(self.klines, self.closeseat, period)
        ta_emas = talib.EMA(self.klines_df[self.closekey], period)
        print(" X-Lib    emas(%d):  %s" % (period, [round(a, self.digits) for a in emas][-self.display_count:]))
        print("TA-Lib    emas(%d):  %s" % (period, [round(a, self.digits) for a in ta_emas][-self.display_count:]))
        for i in range(-self.display_count, 0):
            self.assertTrue(abs(emas[i] - ta_emas.values[i]) < 0.01)

        nbiases = ic.py_biases(closes, emas)
        ta_nbiases = ic.pd_biases(pd.to_numeric(self.klines_df[self.closekey]), ta_emas)
        print(" X-Lib nbiases(%d):  %s" % (period, [round(a, 4) for a in nbiases][-self.display_count:]))
        print("TA-Lib nbiases(%d):  %s" % (period, [round(a, 4) for a in ta_nbiases][-self.display_count:]))
        for i in range(-self.display_count, 0):
            self.assertTrue(abs(nbiases[i] - ta_nbiases.values[i]) < 0.01)


    def _test_perf_xlib_rsi(self):
        for i in range(self.count):
            klines = self.md.get_klines(self.symbol, self.interval, 150 + self.display_count)

            py_rsis = ic.py_rsis(klines, self.closeseat)
            py_rsis = [round(a, 3) for a in py_rsis][-self.display_count:]

            self.md.tick_time += self.td

    def _test_perf_talib_rsi(self):
        for i in range(self.count):
            klines = self.md.get_klines(self.symbol, self.interval, 150 + self.display_count)
            klines_df = pd.DataFrame(klines, columns=self.md.get_kline_column_names())

            ta_rsis = talib.RSI(klines_df[self.closekey])
            ta_rsis = [round(a, 3) for a in ta_rsis][-self.display_count:]

            self.md.tick_time += self.td

    def perf_py_ema(self):
        period = 55
        for i in range(self.count):
            klines = self.md.get_klines(self.symbol, self.interval, 150 + self.display_count)

            emas = ic.py_emas(self.klines, self.closeseat, period)

            self.md.tick_time += self.td

    def perf_xlib_ema(self):
        period = 55
        for i in range(self.count):
            klines = self.md.get_klines(self.symbol, self.interval, 150 + self.display_count)

            closes = [float(k[self.closeseat]) for k in klines]
            emas = xti.EMA(closes, period)

            self.md.tick_time += self.td

    def perf_xlib_ema_kl(self):
        period = 55
        for i in range(self.count):
            klines = self.md.get_klines(self.symbol, self.interval, 150 + self.display_count)

            #emas = xti.EMA_KL(self.klines, self.closeseat, period)

            self.md.tick_time += self.td

if __name__ == '__main__':
    unittest.main()
