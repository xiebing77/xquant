#!/usr/bin/python
"""运行环境引擎"""
import matplotlib.pyplot as plt
import matplotlib.dates as dts
from matplotlib import gridspec
import mpl_finance as mpf
import mplfinance as mpf2
import pandas as pd
import talib
from datetime import datetime,timedelta
from pprint import pprint
import common.log as log
import utils.tools as ts
import utils.indicator as ic
import common.xquant as xq
import common.kline as kl
import common.bill as bl
from db.mongodb import get_mongodb
from engine.order import *
from setup import *
from chart.overlap_studies import *
from chart.price_transform import *
from chart.momentum_indicators import *
from chart.volume_indicators import *
from chart.volatility_indicators import *
from chart.cycle_indicators import *
from chart.other_indicators import *


def chart_mpf2(title, args, symbol, ordersets, klines, md, display_count):
    klines_df = pd.DataFrame(klines, columns=md.kline_column_names)
    klines_df.index = pd.to_datetime(klines_df.index)
    klines_df[md.kline_key_open] = pd.to_numeric(klines_df[md.kline_key_open])
    klines_df[md.kline_key_close] = pd.to_numeric(klines_df[md.kline_key_close])
    klines_df[md.kline_key_high] = pd.to_numeric(klines_df[md.kline_key_high])
    klines_df[md.kline_key_low] = pd.to_numeric(klines_df[md.kline_key_low])
    klines_df[md.kline_key_volume] = pd.to_numeric(klines_df[md.kline_key_volume])

    s = mpf2.make_mpf_style(base_mpf_style='classic', rc={'figure.facecolor':'lightgray'})
    mpf2.plot(klines_df, type='candle', figscale=1.2, figratio=(8,5), title=title, style=s, volume=True)
    return


def chart_mpf(title, args, symbol, ordersets, klines, md, display_count, signalsets=[]):
    klines_df = pd.DataFrame(klines, columns=md.kline_column_names)
    opens = klines_df[md.kline_key_open][-display_count:]
    closes = klines_df[md.kline_key_close][-display_count:]
    opens = pd.to_numeric(opens)
    closes = pd.to_numeric(closes)
    base_close = closes.values[0]
    open_times = [md.get_time_from_data_ts(float(open_time)) for open_time in klines_df[md.kline_key_open_time][-display_count:]]
    close_times = [md.get_time_from_data_ts(float(close_time)) for close_time in klines_df[md.kline_key_close_time][-display_count:]]

    cols = (1 + get_momentum_indicators_count(args)
        + get_volume_indicators_count(args)
        + get_volatility_indicators_count(args)
        + get_cycle_indicators_count(args)
        + get_other_indicators_count(args)
        + len(ordersets))

    if args.okls:
        cols += len(args.okls)
    if cols == 1:
        args.volume = True
    if args.volume:
        cols += 1
    print("cols: ", cols)

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
    fig, axes = plt.subplots(cols, 1, sharex=True)
    fig.subplots_adjust(left=0.05, bottom=0.04, right=1, top=1, wspace=0, hspace=0)
    fig.suptitle(title)

    i = 0
    ax_kl = axes[0]
    quotes = []
    for k in klines[-display_count:]:
        d = md.get_time_from_data_ts(k[md.get_kline_seat_open_time()])
        quote = (dts.date2num(d), float(k[md.get_kline_seat_open()]), float(k[md.get_kline_seat_close()]), float(k[md.get_kline_seat_high()]), float(k[md.get_kline_seat_low()]))
        quotes.append(quote)
    mpf.candlestick_ochl(ax_kl, quotes, width=0.02, colorup='g', colordown='r')
    ax_kl.grid(True)
    ax_kl.autoscale_view()
    ax_kl.xaxis_date()
    ax_kl.set_yscale('log')
    for orders in ordersets:
        ax_kl.plot([datetime.fromtimestamp(order["create_time"]) for order in orders], [(order["deal_value"] / order["deal_amount"]) for order in orders], "o--")
    #pprint(signalsets)
    for key in signalsets:
        signals = signalsets[key]
        #pprint(signals)
        if "color" in signals[0]:
            c = signals[0]["color"]
        else:
            c = None
        ax_kl.plot([signal["create_time"] for signal in signals], [signal["price"] for signal in signals], "o", color=c)
    name_add = handle_overlap_studies(args, ax_kl, klines_df, close_times, display_count)
    handle_price_transform(args, ax_kl, klines_df, close_times, display_count)
    ax_kl.set_ylabel('price'+name_add)

    if args.okls:
        for interval_mi in args.okls:
            i += 1
            ax_kl = axes[i]
            print(interval_mi)
            count_mi = display_count*12
            klines_mi = md.get_klines(symbol, interval_mi, count_mi)
            klines_mi_df = pd.DataFrame(klines_mi, columns=md.kline_column_names)
            close_times_mi = [md.get_time_from_data_ts(float(close_time)) for close_time in klines_mi_df[md.kline_key_close_time][-count_mi:]]
            quotes = []
            for k in klines_mi[-count_mi:]:
                d = md.get_time_from_data_ts(k[md.get_kline_seat_open_time()])
                quote = (dts.date2num(d), float(k[md.get_kline_seat_open()]), float(k[md.get_kline_seat_close()]), float(k[md.get_kline_seat_high()]), float(k[md.get_kline_seat_low()]))
                quotes.append(quote)
            mpf.candlestick_ochl(ax_kl, quotes, width=0.02, colorup='g', colordown='r')
            ax_kl.grid(True)
            ax_kl.autoscale_view()
            ax_kl.xaxis_date()
            ax_kl.set_yscale('log')
            for orders in ordersets:
                ax_kl.plot([datetime.fromtimestamp(order["create_time"]) for order in orders], [(order["deal_value"] / order["deal_amount"]) for order in orders], "o--")
            #pprint(signalsets)
            for key in signalsets:
                signals = signalsets[key]
                #pprint(signals)
                if "color" in signals[0]:
                    c = signals[0]["color"]
                else:
                    c = None
                ax_kl.plot([signal["create_time"] for signal in signals], [signal["price"] for signal in signals], "o", color=c)
            name_add = handle_overlap_studies(args, ax_kl, klines_mi_df, close_times_mi, count_mi)
            ax_kl.set_ylabel(interval_mi+name_add)


    if args.volume:
        i += 1
        axes[i].set_ylabel('volume')
        axes[i].grid(True)
        volumes = [float(volume) for volume in klines_df[md.kline_key_volume][-display_count:]]
        #axes[i].plot(open_times, volumes, "g", drawstyle="steps", label=md.kline_key_volume)
        axes[i].bar(open_times, volumes, label=md.kline_key_volume, width=0.1)

    handle_momentum_indicators(args, axes, i, klines_df, close_times, display_count)
    i += get_momentum_indicators_count(args)

    handle_volume_indicators(args, axes, i, klines_df, close_times, display_count)
    i += get_volume_indicators_count(args)

    handle_volatility_indicators(args, axes, i, klines_df, close_times, display_count)
    i += get_volatility_indicators_count(args)

    handle_cycle_indicators(args, axes, i, klines_df, close_times, display_count)
    i += get_cycle_indicators_count(args)

    handle_other_indicators(args, axes, i, klines_df, close_times, display_count)
    i += get_other_indicators_count(args)

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
    for orders in ordersets:
        i += 1
        axes[i].set_ylabel('profit rate')
        axes[i].grid(True)
        #axes[i].set_label(["position rate", "profit rate"])
        #axes[i].plot(trade_times ,[round(100*order["pst_rate"], 2) for order in orders], "k-", drawstyle="steps-post", label="position")
        trade_times = [datetime.fromtimestamp(order["create_time"]) for order in orders]
        axes[i].plot(trade_times,[round(100*order[POSITON_KEY][POSITON_PROFIT_RATE_KEY], 2) for order in orders], "b", drawstyle="steps", label="single profit")
        if args.tp:
            axes[i].plot(trade_times, [round(100*order[POSITON_KEY][TOTAL_PROFIX_RATE_KEY], 2) for order in orders], "r--")

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


def chart(title, md, symbol, interval, start_time, end_time, ordersets, args, signalsets=[]):
    display_count = int((end_time - start_time).total_seconds()/kl.get_interval_seconds(interval))
    print("display_count: %s" % display_count)
    
    #klines = md.get_klines(symbol, interval, 150+display_count)
    klines = md.get_original_klines(kl.get_kline_collection(symbol, interval), start_time, end_time)
    #print("klines: %s"%klines)
    if len(klines) > 0:
        chart_mpf(title, args, symbol, ordersets, klines, md, display_count, signalsets)

def chart_add_all_argument(parser):
    add_argument_overlap_studies(parser)
    add_argument_price_transform(parser)
    add_argument_momentum_indicators(parser)
    add_argument_volume_indicators(parser)
    add_argument_volatility_indicators(parser)
    add_argument_cycle_indicators(parser)
    add_argument_other_indicators(parser)

