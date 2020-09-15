#!/usr/bin/python
import sys
sys.path.append('../')

from datetime import datetime
import unittest
import pandas as pd
import talib

from md.dbmd import DBMD
import utils.indicator as ic
import utils.ti as ti
import common.xquant as xq
import common.kline as kl
import exchange.exchange  as ex

def print_test_title(name):
    print("\n", "-"*8, "test", name, "-"*100)


class TestIndicator(unittest.TestCase):

    def setUp(self):
        self.symbol = "eth_usdt"
        self.digits = 6
        self.interval = kl.KLINE_INTERVAL_1DAY
        self.display_count = 10

        exchange_name = ex.BINANCE_SPOT_EXCHANGE_NAME
        self.md = DBMD(exchange_name)
        self.md.tick_time = datetime(2019, 1, 1, 8)

        self.klines = self.md.get_klines(self.symbol, self.interval, 150 + self.display_count)

        self.klines_df = pd.DataFrame(self.klines, columns=self.md.get_kline_column_names())

        self.closeseat = self.md.get_kline_seat_close()
        self.highseat = self.md.get_kline_seat_high()
        self.lowseat = self.md.get_kline_seat_low()

        self.closekey = ex.get_kline_key_close(exchange_name)
        self.highkey = ex.get_kline_key_high(exchange_name)
        self.lowkey = ex.get_kline_key_low(exchange_name)

        self.count = 5000
        self.steps = 1
        self.td = kl.get_interval_timedelta(kl.KLINE_INTERVAL_1MINUTE) * self.steps


    def tearDown(self):
        pass

    def test_ma(self):
        print_test_title("ma")
        period = 55

        kls =self.klines
        ma_key = ti.MA(kls, self.closekey, period)
        print("    ti  mas:  ", [round(kl[ma_key], self.digits) for kl in kls[-self.display_count:]])

        tas = talib.MA(self.klines_df[self.closekey], period)
        print("TA-Lib  mas:  ", [round(a, self.digits) for a in tas][-self.display_count:])

        for i in range(-self.display_count, 0):
            self.assertTrue(abs(kls[i][ma_key] - tas.values[i]) < 0.01)


    def test_ema(self):
        print_test_title("ema")
        period = 55

        kls =self.klines
        ema_key = ti.EMA(kls, self.closekey, period)
        print("    ti  emas:  ", [round(kl[ema_key], self.digits) for kl in kls[-self.display_count:]])

        tas = talib.EMA(self.klines_df[self.closekey], period)
        print("TA-Lib  emas:  ", [round(a, self.digits) for a in tas][-self.display_count:])

        for i in range(-self.display_count, 0):
            self.assertTrue(abs(kls[i][ema_key] - tas.values[i]) < 0.01)


    def test_bias(self):
        print_test_title("bias")
        period_s = 21
        period_l = 55

        kls =self.klines
        ema_s_key = ti.EMA(kls, self.closekey, period_s)
        ta_semas = talib.EMA(self.klines_df[self.closekey], period_s)
        print("    ti       semas(%d):  %s" % (period_s, [round(kl[ema_s_key], self.digits) for kl in kls[-self.display_count:]]))
        print("TA-Lib       semas(%d):  %s" % (period_s, [round(a, self.digits) for a in ta_semas][-self.display_count:]))
        for i in range(-self.display_count, 0):
            self.assertTrue(abs(kls[i][ema_s_key] - ta_semas.values[i]) < 0.01)

        ema_l_key = ti.EMA(kls, self.closekey, period_l)
        ta_lemas = talib.EMA(self.klines_df[self.closekey], period_l)
        print("    ti       lemas(%d):  %s" % (period_l, [round(kl[ema_l_key], self.digits) for kl in kls[-self.display_count:]]))
        print("TA-Lib       lemas(%d):  %s" % (period_l, [round(a, self.digits) for a in ta_lemas][-self.display_count:]))
        for i in range(-self.display_count, 0):
            self.assertTrue(abs(kls[i][ema_l_key] - ta_lemas.values[i]) < 0.01)

        bias_sl_key = ti.BIAS(kls, self.closekey, period_s, period_l)
        ta_biases = ic.pd_biases(ta_semas, ta_lemas)
        print("    ti  biases(%d, %d):  %s" % (period_s, period_l, [round(kl[bias_sl_key], self.digits) for kl in kls[-self.display_count:]]))
        print("TA-Lib  biases(%d, %d):  %s" % (period_s, period_l, [round(a, self.digits) for a in ta_biases][-self.display_count:]))
        for i in range(-self.display_count, 0):
            self.assertTrue(abs(kls[i][bias_sl_key] - ta_biases.values[i]) < 0.01)


    def test_rsi(self):
        print_test_title("rsi")

        kls =self.klines
        rsi_key = ti.RSI(kls, self.closekey)
        ta_rsis = talib.RSI(self.klines_df[self.closekey])
        print("    ti  rsis:  ", [round(kl[rsi_key], self.digits) for kl in kls[-self.display_count:]])
        print("TA-Lib  rsis:  ", [round(a, self.digits) for a in ta_rsis][-self.display_count:])

        for i in range(-self.display_count, 0):
            self.assertTrue(abs(kls[i][rsi_key] - ta_rsis.values[i]) < 0.01)

    def test_macd(self):
        print_test_title("macd")

        kls =self.klines
        dif_key, signal_key, hist_key = ti.MACD(kls, self.closekey)
        difs, signals, hists = talib.MACD(self.klines_df[self.closekey])
        print("    ti  macd difs:  ", [round(kl[dif_key], self.digits) for kl in kls[-self.display_count:]])
        print("TA-Lib  macd difs:  ", [round(a, self.digits) for a in difs][-self.display_count:])

        print("    ti  macd signals:  ", [round(kl[signal_key], self.digits) for kl in kls[-self.display_count:]])
        print("TA-Lib  macd signals:  ", [round(a, self.digits) for a in signals][-self.display_count:])

        print("    ti  macd hists:  ", [round(kl[hist_key], self.digits) for kl in kls[-self.display_count:]])
        print("TA-Lib  macd hists:  ", [round(a, self.digits) for a in hists][-self.display_count:])

        for i in range(-self.display_count, 0):
            self.assertTrue(abs(kls[i][dif_key] - difs.values[i]) < 0.01)
            self.assertTrue(abs(kls[i][signal_key] - signals.values[i]) < 0.01)
            self.assertTrue(abs(kls[i][hist_key] - hists.values[i]) < 0.01)

    def perf_macd(self):
        for i in range(self.count):
            kls = self.md.get_klines(self.symbol, self.interval, 150 + self.display_count)
            dif_key, signal_key, hist_key = ti.MACD(kls, self.closekey)

            kls_df = pd.DataFrame(kls, columns=self.md.get_kline_column_names())
            difs, signals, hists = talib.MACD(kls_df[self.closekey])

            i = -1
            self.assertTrue(abs(kls[i][dif_key] - difs.values[i]) < 0.01)
            self.assertTrue(abs(kls[i][signal_key] - signals.values[i]) < 0.01)
            self.assertTrue(abs(kls[i][hist_key] - hists.values[i]) < 0.01)

            self.md.tick_time += self.td

    def test_kd(self):
        print_test_title("kd")
        period = 9
        kls =self.klines
        kkey, dkey = ti.KD(kls, self.closekey, self.highkey, self.lowkey, period)
        '''
        kls_df = self.klines_df
        slowk, slowd = talib.STOCH(high=kls_df[self.highkey], low=kls_df[self.lowkey], close=kls_df[self.closekey],
            fastk_period=period, slowk_period=3, slowk_matype=0, slowd_period=3, slowd_matype=0)
        '''
        kds = ic.py_kdj(kls, self.highseat, self.lowseat, self.closeseat)


        print("      ti  kd ks:  ", [round(kl[kkey], self.digits) for kl in kls[-self.display_count:]])
        #print("TA-Lib  kd ks:  ", [round(k, self.digits) for k in slowk][-self.display_count:])
        print("indicator kd ks:  ", [round(kd[1], self.digits) for kd in kds[-self.display_count:]])

        print("      ti  kd ds:  ", [round(kl[dkey], self.digits) for kl in kls[-self.display_count:]])
        #print("TA-Lib  kd ds:  ", [round(d, self.digits) for d in slowd][-self.display_count:])
        print("indicator kd ds:  ", [round(kd[2], self.digits) for kd in kds[-self.display_count:]])

        for i in range(-self.display_count, 0):
            #self.assertTrue(abs(kls[i][kkey] - slowk.values[i]) < 0.01)
            #self.assertTrue(abs(kls[i][dkey] - slowd.values[i]) < 0.01)
            self.assertTrue(abs(kls[i][kkey] - kds[i][1]) < 0.01)
            self.assertTrue(abs(kls[i][dkey] - kds[i][2]) < 0.01)

    def _test_atr(self):
        name = "atr"
        period = 14
        print_test_title(name)

        kls =self.klines
        ti_key = ti._ATR(kls, self.highkey, self.lowkey, self.closekey, period)
        tas = talib.ATR(self.klines_df[self.highkey], self.klines_df[self.lowkey], self.klines_df[self.closekey], timeperiod=period)
        print("    ti  %ss:  %s" % (name, [round(kl[ti_key], self.digits) for kl in kls[-self.display_count:]]))
        print("TA-Lib  %ss:  %s" % (name, [round(a, self.digits) for a in tas][-self.display_count:]))

        for i in range(-self.display_count, 0):
            self.assertTrue(abs(kls[i][ti_key] - tas.values[i]) < 0.01)

    def test_trix(self):
        name = "trix"
        print_test_title(name)
        period = 30

        kls =self.klines
        ti_key = ti.TRIX(kls, self.closekey, period)
        tas = talib.TRIX(self.klines_df[self.closekey], timeperiod=period)
        print("    ti  %ss:  %s" % (name, [round(kl[ti_key], self.digits) for kl in kls[-self.display_count:]]))
        print("TA-Lib  %ss:  %s" % (name, [round(a, self.digits) for a in tas][-self.display_count:]))

        for i in range(-self.display_count, 0):
            self.assertTrue(abs(kls[i][ti_key] - tas.values[i]) < 0.01)


if __name__ == '__main__':
    unittest.main()
