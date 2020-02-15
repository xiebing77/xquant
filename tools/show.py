#!/usr/bin/python3
import sys
sys.path.append('../')
import argparse
import utils.tools as ts
import utils.indicator as ic
import common.xquant as xq
from md.dbmd import DBMD

import matplotlib.pyplot as plt
import matplotlib.dates as dts
from matplotlib import gridspec
import mpl_finance as mpf
import pandas as pd
import talib

from datetime import datetime,timedelta

def show(args, klines, kline_column_names, display_count):
    for index, value in enumerate(kline_column_names):
        if value == "high":
            highindex = index
        if value == "low":
            lowindex = index
        if value == "open":
            openindex = index
        if value == "close":
            closeindex = index
        if value == "volume":
            volumeindex = index
        if value == "open_time":
            opentimeindex = index


    klines_df = pd.DataFrame(klines, columns=kline_column_names)
    open_times = [datetime.fromtimestamp((float(open_time)/1000)) for open_time in klines_df["open_time"][-display_count:]]
    close_times = [datetime.fromtimestamp((float(close_time)/1000)) for close_time in klines_df["close_time"][-display_count:]]

    fig, axes = plt.subplots(4, 1, sharex=True)
    fig.subplots_adjust(left=0.04, bottom=0.04, right=1, top=1, wspace=0, hspace=0)

    quotes = []
    for k in klines[-display_count:]:
        d = datetime.fromtimestamp(k[0]/1000)
        quote = (dts.date2num(d), float(k[1]), float(k[4]), float(k[2]), float(k[3]))
        quotes.append(quote)

    i = -1

    # k line
    i += 1
    mpf.candlestick_ochl(axes[i], quotes, width=0.02, colorup='g', colordown='r')
    axes[i].set_ylabel('price')
    axes[i].grid(True)
    axes[i].autoscale_view()
    axes[i].xaxis_date()

    e_p  = 26
    emas = talib.EMA(klines_df["close"], timeperiod=e_p)
    s_emas = talib.EMA(klines_df["close"], timeperiod=e_p/2)
    emas = emas[-display_count:]
    s_emas = s_emas[-display_count:]
    axes[i].plot(close_times, emas, "b--", label="%sEMA" % (e_p))
    axes[i].plot(close_times, s_emas, "c--", label="%sEMA" % (e_p/2))

    if not args.tp:
        tp = 40
    else:
        tp = int(args.tp)
    t_emas = talib.EMA(klines_df["close"], timeperiod=tp)
    t_emas = t_emas[-display_count:]
    axes[i].plot(close_times, t_emas, "m--", label="%sEMA" % (tp))

    # macd
    klines_df = ic.pd_macd(klines_df)
    difs = [round(a, 2) for a in klines_df["dif"]]
    deas = [round(a, 2) for a in klines_df["dea"]]
    macds = [round(a, 2) for a in klines_df["macd"]]
    difs = difs[-display_count:]
    deas = deas[-display_count:]
    macds = macds[-display_count:]
    i += 1
    axes[i].set_ylabel('macd')
    axes[i].grid(True)
    axes[i].plot(close_times, difs, "y", label="dif")
    axes[i].plot(close_times, deas, "b", label="dea")
    axes[i].plot(close_times, macds, "r", drawstyle="steps", label="macd")

    # rsi
    i += 1
    axes[i].set_ylabel('rsi')
    axes[i].grid(True)
    rsis = talib.RSI(klines_df["close"], timeperiod=14)
    rsis = [round(a, 2) for a in rsis][-display_count:]
    axes[i].plot(close_times, rsis, "r", label="rsi")


    rs2 = ic.py_rsis(klines, closeindex, period=14)
    rs2 = [round(a, 2) for a in rs2][-display_count:]
    axes[i].plot(close_times, rs2, "y", label="rsi2")
    """
    fastk, fastd = talib.STOCHRSI(klines_df["close"], timeperiod=14)
    rsifks = [round(a, 2) for a in fastk][-display_count:]
    rsifds = [round(a, 2) for a in fastd][-display_count:]
    axes[i].plot(close_times, rsifks, "b", label="rsi")
    axes[i].plot(close_times, rsifds, "y", label="rsi")
    """
    # kdj
    i += 1
    axes[i].set_ylabel('kdj')
    axes[i].grid(True)
    """
    ks, ds = talib.STOCH(klines_df["high"], klines_df["low"], klines_df["close"],
        fastk_period=9, slowk_period=3, slowk_matype=0, slowd_period=3, slowd_matype=0)
    js = ks - ds
    """
    ks, ds, js = ic.pd_kdj(klines_df)
    ks = [round(a, 2) for a in ks][-display_count:]
    ds = [round(a, 2) for a in ds][-display_count:]
    js = [round(a, 2) for a in js][-display_count:]
    axes[i].plot(close_times, ks, "b", label="k")
    axes[i].plot(close_times, ds, "y", label="d")
    axes[i].plot(close_times, js, "m", label="j")

    """
    # willr
    willrs = talib.WILLR(klines_df["high"], klines_df["low"], klines_df["close"], timeperiod=14)
    willrs = [round(a, 2) for a in willrs][-display_count:]
    i += 1
    axes[i].set_ylabel('willr')
    axes[i].grid(True)
    axes[i].plot(close_times, willrs, "y", label="willrs")
    """

    plt.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='show')
    parser.add_argument('-e', help='exchange')
    parser.add_argument('-s', help='symbol (btc_usdt)')
    parser.add_argument('-i', help='interval')
    parser.add_argument('-r', help='time range')
    parser.add_argument('-tp', help='trend period')
    args = parser.parse_args()
    # print(args)

    if not (args.r and args.i and args.s):
        parser.print_help()
        exit(1)

    if not args.e:
        exchange = "binance"
        open_hour = 8
    else:
        exchange = args.e
        open_hour = 8

    interval = args.i
    start_time, end_time = ts.parse_date_range(args.r)
    display_count = int((end_time - start_time).total_seconds()/xq.get_interval_seconds(interval))
    print("display_count: %s" % display_count)


    md = DBMD(exchange)
    md.tick_time = datetime.now()
    pre_count = 150
    klines = md.get_klines(args.s, interval, pre_count+display_count, start_time-xq.get_timedelta(interval, pre_count))

    show(args, klines, md.kline_column_names, display_count)

