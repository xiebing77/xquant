#!/usr/bin/python3
import sys
sys.path.append('../')
import argparse
import utils.tools as ts
import common.xquant as xq
import common.kline as kl
from md.dbmd import DBMD
from exchange.exchange import exchange_names, BINANCE_SPOT_EXCHANGE_NAME

from datetime import datetime,timedelta
from chart.chart import chart, chart_add_all_argument


'''
def show(args, klines, kline_column_names, display_count, disp_ic_keys):
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

    fig, axes = plt.subplots(len(disp_ic_keys)+1, 1, sharex=True)
    fig.subplots_adjust(left=0.05, bottom=0.04, right=1, top=1, wspace=0, hspace=0)
    fig.suptitle(args.s + '    ' + args.i)

    quotes = []
    for k in klines[-display_count:]:
        d = datetime.fromtimestamp(k[0]/1000)
        quote = (dts.date2num(d), float(k[1]), float(k[4]), float(k[2]), float(k[3]))
        quotes.append(quote)

    i = -1

    # kine
    i += 1
    ax = axes[i]
    mpf.candlestick_ochl(axes[i], quotes, width=0.02, colorup='g', colordown='r')
    ax.set_ylabel('price')
    ax.grid(True)
    ax.autoscale_view()
    ax.xaxis_date()


    handle_overlap_studies(args, ax, klines_df, close_times, display_count)

    """
    if args.EBANDS: # BANDS
        name = 'EBANDS'
        upperband, middleband, lowerband = tal.EBANDS(klines_df, timeperiod=26)
        ax.plot(close_times, middleband[-display_count:], "b--", label=name)
        ax.plot(close_times, upperband[-display_count:], 'y--', label=name+' upperband')
        ax.plot(close_times, lowerband[-display_count:], 'y--', label=name+' lowerband')
    """

    ic_key = 'macd'
    if ic_key in disp_ic_keys:
        i += 1
        ax = axes[i]
        ax.set_ylabel('macd')
        ax.grid(True)

        klines_df = ic.pd_macd(klines_df)
        difs = [round(a, 2) for a in klines_df["dif"]]
        deas = [round(a, 2) for a in klines_df["dea"]]
        macds = [round(a, 2) for a in klines_df["macd"]]
        ax.plot(close_times, difs[-display_count:], "y", label="dif")
        ax.plot(close_times, deas[-display_count:], "b", label="dea")
        ax.plot(close_times, macds[-display_count:], "r", drawstyle="steps", label="macd")

    ic_key = 'RSI'
    if ic_key in disp_ic_keys:
        i += 1
        ax = axes[i]
        ax.set_ylabel(ic_key)
        ax.grid(True)
        rsis = talib.RSI(klines_df["close"], timeperiod=14)
        rsis = [round(a, 2) for a in rsis][-display_count:]
        ax.plot(close_times, rsis, "r", label=ic_key)
        ax.plot(close_times, [70]*len(rsis), '-', color='r')
        ax.plot(close_times, [30]*len(rsis), '-', color='r')

        """
        rs2 = ic.py_rsis(klines, closeindex, period=14)
        rs2 = [round(a, 2) for a in rs2][-display_count:]
        axes[i].plot(close_times, rs2, "y", label="rsi2")
        """


    """
    fastk, fastd = talib.STOCHRSI(klines_df["close"], timeperiod=14)
    rsifks = [round(a, 2) for a in fastk][-display_count:]
    rsifds = [round(a, 2) for a in fastd][-display_count:]
    axes[i].plot(close_times, rsifks, "b", label="rsi")
    axes[i].plot(close_times, rsifds, "y", label="rsi")
    """

    ic_key = 'KDJ'
    if ic_key in disp_ic_keys:
        i += 1
        ax = axes[i]
        ax.set_ylabel(ic_key)
        ax.grid(True)
        """
        ks, ds = talib.STOCH(klines_df["high"], klines_df["low"], klines_df["close"],
            fastk_period=9, slowk_period=3, slowk_matype=0, slowd_period=3, slowd_matype=0)
        js = ks - ds
        """
        ks, ds, js = ic.pd_kdj(klines_df)
        ks = [round(a, 2) for a in ks][-display_count:]
        ds = [round(a, 2) for a in ds][-display_count:]
        js = [round(a, 2) for a in js][-display_count:]
        ax.plot(close_times, ks, "b", label="K")
        ax.plot(close_times, ds, "y", label="D")
        ax.plot(close_times, js, "m", label="J")

    # Volume Indicator
    ic_key = 'AD'
    if ic_key in disp_ic_keys:
        real = talib.AD(klines_df["high"], klines_df["low"], klines_df["close"], klines_df["volume"])
        i += 1
        ts.ax(axes[i], ic_key, close_times, real[-display_count:], "y:")

    ic_key = 'ADOSC'
    if ic_key in disp_ic_keys:
        real = talib.ADOSC(klines_df["high"], klines_df["low"], klines_df["close"], klines_df["volume"], fastperiod=3, slowperiod=10)
        i += 1
        ts.ax(axes[i], ic_key, close_times, real[-display_count:], "y:")

    ic_key = 'OBV'
    if ic_key in disp_ic_keys:
        real = talib.OBV(klines_df["close"], klines_df["volume"])
        i += 1
        ts.ax(axes[i], ic_key, close_times, real[-display_count:], "y:")

    # Volatility Indicator
    ic_key = 'ATR'
    if ic_key in disp_ic_keys:
        real = talib.ATR(klines_df["high"], klines_df["low"], klines_df["close"], timeperiod=14)
        i += 1
        ts.ax(axes[i], ic_key, close_times, real[-display_count:], "y:")
    ic_key = 'NATR'
    if ic_key in disp_ic_keys:
        real = talib.NATR(klines_df["high"], klines_df["low"], klines_df["close"], timeperiod=14)
        i += 1
        ts.ax(axes[i], ic_key, close_times, real[-display_count:], "y:")
    ic_key = 'TRANGE'
    if ic_key in disp_ic_keys:
        real = talib.TRANGE(klines_df["high"], klines_df["low"], klines_df["close"])
        i += 1
        ts.ax(axes[i], ic_key, close_times, real[-display_count:], "y:")

    # Price Transform
    ic_key = 'AVGPRICE'
    if ic_key in disp_ic_keys:
        real = talib.AVGPRICE(klines_df["open"], klines_df["high"], klines_df["low"], klines_df["close"])
        i += 1
        ts.ax(axes[i], ic_key, close_times, real[-display_count:], "y:")
    ic_key = 'MEDPRICE'
    if ic_key in disp_ic_keys:
        real = talib.MEDPRICE(klines_df["high"], klines_df["low"])
        i += 1
        ts.ax(axes[i], ic_key, close_times, real[-display_count:], "y:")
    ic_key = 'TYPPRICE'
    if ic_key in disp_ic_keys:
        real = talib.TYPPRICE(klines_df["high"], klines_df["low"], klines_df["close"])
        i += 1
        ts.ax(axes[i], ic_key, close_times, real[-display_count:], "y:")
    ic_key = 'WCLPRICE'
    if ic_key in disp_ic_keys:
        real = talib.WCLPRICE(klines_df["high"], klines_df["low"], klines_df["close"])
        i += 1
        ts.ax(axes[i], ic_key, close_times, real[-display_count:], "y:")


    # Cycle Indicator
    ic_key = 'HT_DCPERIOD'
    if ic_key in disp_ic_keys:
        real = talib.HT_DCPERIOD(klines_df["close"])
        i += 1
        ts.ax(axes[i], ic_key, close_times, real[-display_count:], "y:")
    ic_key = 'HT_DCPHASE'
    if ic_key in disp_ic_keys:
        real = talib.HT_DCPHASE(klines_df["close"])
        i += 1
        ts.ax(axes[i], ic_key, close_times, real[-display_count:], "y:")
    ic_key = 'HT_PHASOR'
    if ic_key in disp_ic_keys:
        real = talib.HT_PHASOR(klines_df["close"])
        i += 1
        ts.ax(axes[i], ic_key, close_times, real[-display_count:], "y:")
    ic_key = 'HT_SINE'
    if ic_key in disp_ic_keys:
        real = talib.HT_SINE(klines_df["close"])
        i += 1
        ts.ax(axes[i], ic_key, close_times, real[-display_count:], "y:")
    ic_key = 'HT_TRENDMODE'
    if ic_key in disp_ic_keys:
        real = talib.HT_TRENDMODE(klines_df["close"])
        i += 1
        ts.ax(axes[i], ic_key, close_times, real[-display_count:], "y:")


    # Statistic
    ic_key = 'BETA'
    if ic_key in disp_ic_keys:
        real = talib.BETA(klines_df["high"], klines_df["low"], timeperiod=5)
        i += 1
        ts.ax(axes[i], ic_key, close_times, real[-display_count:], "y:")
    ic_key = 'CORREL'
    if ic_key in disp_ic_keys:
        real = talib.CORREL(klines_df["high"], klines_df["low"], timeperiod=30)
        i += 1
        ts.ax(axes[i], ic_key, close_times, real[-display_count:], "y:")
    ic_key = 'LINEARREG'
    if ic_key in disp_ic_keys:
        real = talib.LINEARREG(klines_df["close"], timeperiod=14)
        i += 1
        ts.ax(axes[i], ic_key, close_times, real[-display_count:], "y:")
    ic_key = 'LINEARREG_ANGLE'
    if ic_key in disp_ic_keys:
        real = talib.LINEARREG_ANGLE(klines_df["close"], timeperiod=14)
        i += 1
        ts.ax(axes[i], ic_key, close_times, real[-display_count:], "y:")
    ic_key = 'LINEARREG_INTERCEPT'
    if ic_key in disp_ic_keys:
        real = talib.LINEARREG_INTERCEPT(klines_df["close"], timeperiod=14)
        i += 1
        ts.ax(axes[i], ic_key, close_times, real[-display_count:], "y:")
    ic_key = 'LINEARREG_SLOPE'
    if ic_key in disp_ic_keys:
        real = talib.LINEARREG_SLOPE(klines_df["close"], timeperiod=14)
        i += 1
        ts.ax(axes[i], ic_key, close_times, real[-display_count:], "y:")
    ic_key = 'STDDEV' # Standard Deviation
    if ic_key in disp_ic_keys:
        real = talib.STDDEV(klines_df["close"], timeperiod=5, nbdev=1)
        i += 1
        ts.ax(axes[i], ic_key, close_times, real[-display_count:], "y:")
    ic_key = 'TSF' # Time Series Forecast
    if ic_key in disp_ic_keys:
        real = talib.TSF(klines_df["close"], timeperiod=14)
        i += 1
        ts.ax(axes[i], ic_key, close_times, real[-display_count:], "y:")
    ic_key = 'VAR' # Variance
    if ic_key in disp_ic_keys:
        real = talib.VAR(klines_df["close"], timeperiod=5, nbdev=1)
        i += 1
        ts.ax(axes[i], ic_key, close_times, real[-display_count:], "y:")


    # Momentum Indicator
    ic_key = 'DX'
    if ic_key in disp_ic_keys:
        dxs = talib.DX(klines_df["high"], klines_df["low"], klines_df["close"], timeperiod=14)
        adxs = talib.ADX(klines_df["high"], klines_df["low"], klines_df["close"], timeperiod=14)
        adxrs = talib.ADXR(klines_df["high"], klines_df["low"], klines_df["close"], timeperiod=14)
        i += 1
        ts.ax(axes[i], ic_key, close_times, dxs[-display_count:], "r:")
        ts.ax(axes[i], ic_key, close_times, adxs[-display_count:], "y:")
        ts.ax(axes[i], ic_key, close_times, adxrs[-display_count:], "k:")

    ic_key = 'APO'
    if ic_key in disp_ic_keys:
        real = talib.APO(klines_df["close"], fastperiod=12, slowperiod=26, matype=0)
        i += 1
        ts.ax(axes[i], ic_key, close_times, real[-display_count:], "y:")

    ic_key = 'AROON'
    if ic_key in disp_ic_keys:
        aroondown, aroonup = talib.AROON(klines_df["high"], klines_df["low"], timeperiod=14)
        i += 1
        ts.ax(axes[i], ic_key+' DOWN', close_times, aroondown[-display_count:], "y:")
        ts.ax(axes[i], ic_key+' UP', close_times, aroonup[-display_count:], "y:")

    ic_key = 'AROONOSC'
    if ic_key in disp_ic_keys:
        real = talib.AROONOSC(klines_df["high"], klines_df["low"], timeperiod=14)
        i += 1
        ts.ax(axes[i], ic_key, close_times, real[-display_count:], "y:")

    ic_key = 'BOP'
    if ic_key in disp_ic_keys:
        real = talib.BOP(klines_df["open"], klines_df["high"], klines_df["low"], klines_df["close"])
        i += 1
        ts.ax(axes[i], ic_key, close_times, real[-display_count:], "y:")

    ic_key = 'CCI'
    if ic_key in disp_ic_keys:
        real = talib.CCI(klines_df["high"], klines_df["low"], klines_df["close"], timeperiod=14)
        i += 1
        ts.ax(axes[i], ic_key, close_times, real[-display_count:], "y:")

    ic_key = 'CMO'
    if ic_key in disp_ic_keys:
        real = talib.CMO(klines_df["close"], timeperiod=14)
        i += 1
        ts.ax(axes[i], ic_key, close_times, real[-display_count:], "y:")

    ic_key = 'MACD'
    if ic_key in disp_ic_keys:
        macd, macdsignal, macdhist = talib.MACD(klines_df["close"],
            fastperiod=12, slowperiod=26, signalperiod=9)
        i += 1
        ts.ax(axes[i], ic_key, close_times, macd[-display_count:], "y")
        ts.ax(axes[i], ic_key, close_times, macdsignal[-display_count:], "b")
        ts.ax(axes[i], ic_key, close_times, macdhist[-display_count:], "r", drawstyle="steps")

    ic_key = 'MACDEXT'
    if ic_key in disp_ic_keys:
        macd, macdsignal, macdhist = talib.MACDEXT(klines_df["close"],
            fastperiod=12, fastmatype=0, slowperiod=26, slowmatype=0, signalperiod=9, signalmatype=0)
        i += 1
        ts.ax(axes[i], ic_key, close_times, macd[-display_count:], "y")
        ts.ax(axes[i], ic_key, close_times, macdsignal[-display_count:], "b")
        ts.ax(axes[i], ic_key, close_times, macdhist[-display_count:], "r", drawstyle="steps")

    ic_key = 'MACDFIX'
    if ic_key in disp_ic_keys:
        macd, macdsignal, macdhist = talib.MACDFIX(klines_df["close"], signalperiod=9)
        i += 1
        ts.ax(axes[i], ic_key, close_times, macd[-display_count:], "y")
        ts.ax(axes[i], ic_key, close_times, macdsignal[-display_count:], "b")
        ts.ax(axes[i], ic_key, close_times, macdhist[-display_count:], "r", drawstyle="steps")

    ic_key = 'MFI'
    if ic_key in disp_ic_keys:
        real = talib.MFI(klines_df["high"], klines_df["low"], klines_df["close"], klines_df["volume"])
        i += 1
        ts.ax(axes[i], ic_key, close_times, real[-display_count:], "y:")

    ic_key = 'MINUS_DI'
    if ic_key in disp_ic_keys:
        real = talib.MINUS_DI(klines_df["high"], klines_df["low"], klines_df["close"], timeperiod=14)
        i += 1
        ts.ax(axes[i], ic_key, close_times, real[-display_count:], "y:")

    ic_key = 'MINUS_DM'
    if ic_key in disp_ic_keys:
        real = talib.MINUS_DM(klines_df["high"], klines_df["low"], timeperiod=14)
        i += 1
        ts.ax(axes[i], ic_key, close_times, real[-display_count:], "y:")

    ic_key = 'MOM'
    if ic_key in disp_ic_keys:
        real = talib.MOM(klines_df["close"], timeperiod=10)
        i += 1
        ts.ax(axes[i], ic_key, close_times, real[-display_count:], "y:")

    ic_key = 'PLUS_DI'
    if ic_key in disp_ic_keys:
        real = talib.PLUS_DI(klines_df["high"], klines_df["low"], klines_df["close"], timeperiod=14)
        i += 1
        ts.ax(axes[i], ic_key, close_times, real[-display_count:], "y:")

    ic_key = 'PLUS_DM'
    if ic_key in disp_ic_keys:
        real = talib.PLUS_DM(klines_df["high"], klines_df["low"], timeperiod=14)
        i += 1
        ts.ax(axes[i], ic_key, close_times, real[-display_count:], "y:")

    ic_key = 'PPO'
    if ic_key in disp_ic_keys:
        real = talib.PPO(klines_df["close"], fastperiod=12, slowperiod=26, matype=0)
        i += 1
        ts.ax(axes[i], ic_key, close_times, real[-display_count:], "y:")

    ic_key = 'ROC'
    if ic_key in disp_ic_keys:
        real1 = talib.ROC(klines_df["close"], timeperiod=10)
        real2 = talib.ROCP(klines_df["close"], timeperiod=10)
        real3 = talib.ROCR(klines_df["close"], timeperiod=10)
        real4 = talib.ROCR100(klines_df["close"], timeperiod=10)
        i += 1
        ts.ax(axes[i], ic_key, close_times, real1[-display_count:], "y:")
        ts.ax(axes[i], ic_key, close_times, real2[-display_count:], "k:")
        ts.ax(axes[i], ic_key, close_times, real3[-display_count:], "m:")
        ts.ax(axes[i], ic_key, close_times, real4[-display_count:], "b:")

    ic_key = 'STOCH'
    if ic_key in disp_ic_keys:
        slowk, slowd = talib.STOCH(klines_df["high"], klines_df["low"], klines_df["close"],
            fastk_period=5, slowk_period=3, slowk_matype=0, slowd_period=3, slowd_matype=0)
        i += 1
        slowj = 3*slowk - 2*slowd
        ts.ax(axes[i], ic_key, close_times, slowk[-display_count:], "b")
        ts.ax(axes[i], ic_key, close_times, slowd[-display_count:], "y")
        ts.ax(axes[i], ic_key, close_times, slowj[-display_count:], "m")

    ic_key = 'STOCHF'
    if ic_key in disp_ic_keys:
        fastk, fastd = talib.STOCHF(klines_df["high"], klines_df["low"], klines_df["close"],
            fastk_period=5, fastd_period=3, fastd_matype=0)
        i += 1
        fastj = 3*fastk - 2*fastd
        ts.ax(axes[i], ic_key, close_times, fastk[-display_count:], "y:")
        ts.ax(axes[i], ic_key, close_times, fastd[-display_count:], "b:")
        ts.ax(axes[i], ic_key, close_times, fastj[-display_count:], "m")

    ic_key = 'STOCHRSI'
    if ic_key in disp_ic_keys:
        fastk, fastd = talib.STOCHRSI(klines_df["close"],
            timeperiod=14, fastk_period=5, fastd_period=3, fastd_matype=0)
        i += 1
        ts.ax(axes[i], ic_key, close_times, fastk[-display_count:], "y:")
        ts.ax(axes[i], ic_key, close_times, fastd[-display_count:], "b:")

    ic_key = 'TRIX'
    if ic_key in disp_ic_keys:
        real = talib.TRIX(klines_df["close"], timeperiod=30)
        i += 1
        ts.ax(axes[i], ic_key, close_times, real[-display_count:], "y:")

    ic_key = 'ULTOSC'
    if ic_key in disp_ic_keys:
        real = talib.ULTOSC(klines_df["high"], klines_df["low"], klines_df["close"], timeperiod1=7, timeperiod2=14, timeperiod3=28)
        i += 1
        ts.ax(axes[i], ic_key, close_times, real[-display_count:], "y:")

    ic_key = 'WILLR'
    if ic_key in disp_ic_keys:
        real = talib.WILLR(klines_df["high"], klines_df["low"], klines_df["close"], timeperiod=14)
        i += 1
        ts.ax(axes[i], ic_key, close_times, real[-display_count:], "y:")

    plt.show()
'''


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='show')
    parser.add_argument('-e', choices=exchange_names, default=BINANCE_SPOT_EXCHANGE_NAME, help='exchange')
    parser.add_argument('-s', help='symbol (btc_usdt)')
    parser.add_argument('-i', help='interval')
    parser.add_argument('-r', help='time range')
    #parser.add_argument('-di', nargs='*', help='display indicators,egg: MACD KDJ RSI')

    parser.add_argument('--volume', action="store_true", help='volume')
    parser.add_argument('--mik', help='micro kline')
    chart_add_all_argument(parser)

    args = parser.parse_args()
    # print(args)

    if not (args.r and args.i and args.s and args.e):
        parser.print_help()
        exit(1)

    symbol = args.s
    interval = args.i
    start_time, end_time = ts.parse_date_range(args.r)
    display_count = int((end_time - start_time).total_seconds()/kl.get_interval_seconds(interval))
    print("display_count: %s" % display_count)

    md = DBMD(args.e)
    md.tick_time = datetime.now()

    title = symbol + '  ' + interval

    ordersets = []
    chart(title, md, symbol, interval, start_time, end_time, ordersets, args)

