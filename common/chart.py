#!/usr/bin/python
"""运行环境引擎"""
import matplotlib.pyplot as plt
import matplotlib.dates as dts
from matplotlib import gridspec
import mpl_finance as mpf
import pandas as pd
import talib
from datetime import datetime,timedelta
import common.log as log
import utils.tools as ts
import utils.indicator as ic
import common.xquant as xq
import common.bill as bl
from db.mongodb import get_mongodb
from setup import *
from common.overlap_studies import *
from common.momentum_indicators import *
from common.volume_indicators import *
from common.volatility_indicators import *


def chart_mpf(title, args, symbol, ordersets, klines, kline_column_names, display_count):
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

    opens = klines_df["open"][-display_count:]
    closes = klines_df["close"][-display_count:]
    opens = pd.to_numeric(opens)
    closes = pd.to_numeric(closes)
    base_close = closes.values[0]

    open_times = [datetime.fromtimestamp((float(open_time)/1000)) for open_time in klines_df["open_time"][-display_count:]]
    close_times = [datetime.fromtimestamp((float(close_time)/1000)) for close_time in klines_df["close_time"][-display_count:]]
    """
    gs = gridspec.GridSpec(8, 1)
    gs.update(left=0.04, bottom=0.04, right=1, top=1, wspace=0, hspace=0)
    axes = [
        plt.subplot(gs[0:-2, :]),
        #plt.subplot(gs[-4:-2, :]),
        plt.subplot(gs[-2:-1, :]),
        plt.subplot(gs[-1, :])
    ]
    """
    cols = 1 + get_momentum_indicators_count(args) + get_volume_indicators_count(args) + get_volatility_indicators_count(args) + len(ordersets)
    fig, axes = plt.subplots(cols, 1, sharex=True)
    fig.subplots_adjust(left=0.05, bottom=0.04, right=1, top=1, wspace=0, hspace=0)
    fig.suptitle(title)

    quotes = []
    for k in klines[-display_count:]:
        d = datetime.fromtimestamp(k[0]/1000)
        quote = (dts.date2num(d), float(k[1]), float(k[4]), float(k[2]), float(k[3]))
        quotes.append(quote)

    i = 0
    mpf.candlestick_ochl(axes[i], quotes, width=0.02, colorup='g', colordown='r')
    axes[i].set_ylabel('price')
    axes[i].grid(True)
    axes[i].autoscale_view()
    axes[i].xaxis_date()
    for orders in ordersets:
        axes[i].plot([order["trade_time"] for order in orders], [(order["deal_value"] / order["deal_amount"]) for order in orders], "o--")
    handle_overlap_studies(args, axes[i], klines_df, close_times, display_count)

    handle_momentum_indicators(args, axes, i, klines_df, close_times, display_count)
    i += get_momentum_indicators_count(args)

    handle_volume_indicators(args, axes, i, klines_df, close_times, display_count)
    i += get_volume_indicators_count(args)

    handle_volatility_indicators(args, axes, i, klines_df, close_times, display_count)
    i += get_volatility_indicators_count(args)

    '''
    ic_key = 'mr'
    if ic_key in disp_ic_keys:
        i += 1
        mrs = [round(a, 4) for a in (klines_df["macd"][-display_count:] / closes)]
        mrs = mrs[-display_count:]
        axes[i].set_ylabel('mr')
        axes[i].grid(True)
        axes[i].plot(close_times, mrs, "r--", label="mr")

        leam_mrs = klines_df["macd"] / emas
        seam_mrs = klines_df["macd"] / s_emas
        leam_mrs = leam_mrs[-display_count:]
        seam_mrs = seam_mrs[-display_count:]
        axes[i].plot(close_times, leam_mrs, "y--", label="leam_mr")
        axes[i].plot(close_times, seam_mrs, "m--", label="seam_mr")

    ic_key = 'difr'
    if ic_key in disp_ic_keys:
        i += 1
        difrs = [round(a, 2) for a in (klines_df["dif"][-display_count:] / closes)]
        dears = [round(a, 2) for a in (klines_df["dea"][-display_count:] / closes)]
        difrs = difrs[-display_count:]
        dears = dears[-display_count:]
        axes[i].set_ylabel('r')
        axes[i].grid(True)
        axes[i].plot(close_times, difrs, "m--", label="difr")
        axes[i].plot(close_times, dears, "m--", label="dear")

    ic_key = 'rsi'
    if ic_key in disp_ic_keys:
        i += 1
        axes[i].set_ylabel('rsi')
        axes[i].grid(True)
        rsis = talib.RSI(klines_df["close"], timeperiod=14)
        rsis = [round(a, 3) for a in rsis][-display_count:]
        axes[i].plot(close_times, rsis, "r", label="rsi")
        axes[i].plot(close_times, [70]*len(rsis), '-', color='r')
        axes[i].plot(close_times, [30]*len(rsis), '-', color='r')

        """
        rs2 = ic.py_rsis(klines, closeindex, period=14)
        rs2 = [round(a, 3) for a in rs2][-display_count:]
        axes[i].plot(close_times, rs2, "y", label="rsi2")

        rs3 = ic.py_rsis2(klines, closeindex, period=14)
        rs3 = [round(a, 3) for a in rs3][-display_count:]
        axes[i].plot(close_times, rs3, "m", label="rsi3")
        """


    '''
    i = cols
    for orders in ordersets:
        i -= 1
        axes[i].set_ylabel('rate')
        axes[i].grid(True)
        #axes[i].set_label(["position rate", "profit rate"])
        #axes[i].plot(trade_times ,[round(100*order["pst_rate"], 2) for order in orders], "k-", drawstyle="steps-post", label="position")
        axes[i].plot([order["trade_time"] for order in orders] ,[round(100*order["floating_profit_rate"], 2) for order in orders], "g", drawstyle="steps", label="profit")

    """
    i += 1
    axes[i].set_ylabel('total profit rate')
    axes[i].grid(True)
    axes[i].plot(trade_times, [round(100*order["total_profit_rate"], 2) for order in orders], "go--")
    axes[i].plot(close_times, [round(100*((close/base_close)-1), 2) for close in closes], "r--")
    """

    """
    trade_times = []
    pst_rates = []
    for i, order in enumerate(orders):
        #补充
        if i > 0 and orders[i-1]["pst_rate"] > 0:
            tmp_trade_date = orders[i-1]["trade_time"].date() + timedelta(days=1)
            while tmp_trade_date < order["trade_time"].date():
                trade_times.append(tmp_trade_date)
                pst_rates.append(orders[i-1]["pst_rate"])
                print("add %s, %s" % (tmp_trade_date, orders[i-1]["pst_rate"]))
                tmp_trade_date += timedelta(days=1)

        # 添加
        trade_times.append(order["trade_time"])
        pst_rates.append(order["pst_rate"])
        print("%s, %s" % (order["trade_time"], order["pst_rate"]))
    plt.bar(trade_times, pst_rates, width= 0.3) # 
    """

    plt.show()


def chart(md, config, start_time, end_time, ordersets, args):
    symbol = config["symbol"]
    interval = config["kline"]["interval"]
    display_count = int((end_time - start_time).total_seconds()/xq.get_interval_seconds(interval))
    print("display_count: %s" % display_count)

    klines = md.get_klines(symbol, interval, 150+display_count)
    title = symbol + '  ' + config['kline']['interval'] + ' ' + config['class_name']
    chart_mpf(title, args, symbol, ordersets, klines, md.kline_column_names, display_count)


