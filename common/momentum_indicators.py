#!/usr/bin/python3

import pandas as pd
import talib

import utils.tools as ts
import utils.indicator as ic


def add_argument_momentum_indicators(parser):
    # Momentum Indicators
    group = parser.add_argument_group('Momentum Indicators')

    group.add_argument('--macd', action="store_true", help='Moving Average Convergence/Divergence')
    group.add_argument('--mr', action="store_true", help='MACD rate')
    group.add_argument('--kdj', action="store_true", help='kdj')

    # talib
    group = parser.add_argument_group('Momentum Indicators (TaLib)')
    group.add_argument('--ADX' , action="store_true", help='Average Directional Movement Index')
    group.add_argument('--ADXR', action="store_true", help='Average Directional Movement Index Rating')
    group.add_argument('--APO' , action="store_true", help='Absolute Price Oscillator')
    group.add_argument('--AROON', action="store_true", help='Aroon')
    group.add_argument('--AROONOSC', action="store_true", help='Aroon Oscillator')
    group.add_argument('--BOP', action="store_true", help='Balance Of Power')
    group.add_argument('--CCI', action="store_true", help='Commodity Channel Index')
    group.add_argument('--CMO', action="store_true", help='Chande Momentum Oscillator')
    group.add_argument('--DX', action="store_true", help='Directional Movement Index')
    group.add_argument('--MACD', action="store_true", help='Moving Average Convergence/Divergence')
    group.add_argument('--MACDEXT', action="store_true", help='MACD with controllable MA type')
    group.add_argument('--MACDFIX', action="store_true", help='Moving Average Convergence/Divergence Fix 12/26')
    group.add_argument('--MFI', action="store_true", help='Money Flow Index')
    group.add_argument('--MINUS_DI', action="store_true", help='Minus Directional Indicator')
    group.add_argument('--MINUS_DM', action="store_true", help='Minus Directional Movement')
    group.add_argument('--MOM', action="store_true", help='Momentum')
    group.add_argument('--PLUS_DI', action="store_true", help='Plus Directional Indicator')
    group.add_argument('--PLUS_DM', action="store_true", help='Plus Directional Movement')
    group.add_argument('--PPO', action="store_true", help='Percentage Price Oscillator')
    group.add_argument('--ROC', action="store_true", help='Rate of change : ((price/prevPrice)-1)*100')
    group.add_argument('--ROCP', action="store_true", help='Rate of change Percentage: (price-prevPrice)/prevPrice')
    group.add_argument('--ROCR', action="store_true", help='Rate of change ratio: (price/prevPrice)')
    group.add_argument('--ROCR100', action="store_true", help='Rate of change ratio 100 scale: (price/prevPrice)*100')
    group.add_argument('--RSI', type=int, nargs='*', help='Relative Strength Index')
    group.add_argument('--STOCH', action="store_true", help='Stochastic')
    group.add_argument('--STOCHF', action="store_true", help='Stochastic Fast')
    group.add_argument('--STOCHRSI', action="store_true", help='Stochastic Relative Strength Index')
    group.add_argument('--TRIX', action="store_true", help='1-day Rate-Of-Change (ROC) of a Triple Smooth EMA')
    group.add_argument('--ULTOSC', action="store_true", help='Ultimate Oscillator')
    group.add_argument('--WILLR', action="store_true", help="Williams' %%R")


def get_momentum_indicators_count(args):
    count = 0

    if args.macd: # macd
        count += 1
    if args.mr: # macd rate
        count += 1
    if args.kdj: # kdj
        count += 1

    if args.ADX: # 
        count += 1
    if args.ADXR: # 
        count += 1
    if args.APO: # 
        count += 1
    if args.AROON: # 
        count += 1
    if args.AROONOSC: # 
        count += 1
    if args.BOP: # 
        count += 1
    if args.CCI: # 
        count += 1
    if args.CMO: # 
        count += 1
    if args.DX: # 
        count += 1
    if args.MACD: # MACD
        count += 1
    if args.MACDEXT: # MACDEXT
        count += 1
    if args.MACDFIX: # MACDFIX
        count += 1
    if args.MFI: # 
        count += 1
    if args.MINUS_DI: # 
        count += 1
    if args.MINUS_DM: # 
        count += 1
    if args.MOM: # 
        count += 1
    if args.PLUS_DI: # 
        count += 1
    if args.PLUS_DM: # 
        count += 1
    if args.PPO: # 
        count += 1
    if args.ROC: # 
        count += 1
    if args.ROCP: # 
        count += 1
    if args.ROCR: # 
        count += 1
    if args.ROCR100: # 
        count += 1
    if args.RSI is not None: # RSI
        count += 1
    if args.STOCH: # 
        count += 1
    if args.STOCHF: # 
        count += 1
    if args.STOCHRSI: # 
        count += 1
    if args.TRIX: # 
        count += 1
    if args.ULTOSC: # 
        count += 1
    if args.WILLR: # 
        count += 1

    return count


def handle_momentum_indicators(args, axes, i, klines_df, close_times, display_count):
    if args.macd: # macd
        name = 'macd'
        klines_df = ic.pd_macd(klines_df)
        difs = [round(a, 2) for a in klines_df["dif"]]
        deas = [round(a, 2) for a in klines_df["dea"]]
        macds = [round(a, 2) for a in klines_df["macd"]]
        i += 1
        axes[i].set_ylabel(name)
        axes[i].grid(True)
        axes[i].plot(close_times, difs[-display_count:], "y", label="dif")
        axes[i].plot(close_times, deas[-display_count:], "b", label="dea")
        axes[i].plot(close_times, macds[-display_count:], "r", drawstyle="steps", label="macd")

    if args.mr: # macd rate
        name = 'macd rate'
        klines_df = ic.pd_macd(klines_df)
        closes = klines_df["close"][-display_count:]
        closes = pd.to_numeric(closes)
        mrs = [round(a, 4) for a in (klines_df["macd"][-display_count:] / closes)]
        i += 1
        axes[i].set_ylabel(name)
        axes[i].grid(True)
        axes[i].plot(close_times, mrs, "r--", label="mr")

    if args.kdj: # kdj
        name = 'kdj'
        ks, ds, js = ic.pd_kdj(klines_df)
        i += 1
        axes[i].set_ylabel(name)
        axes[i].grid(True)
        axes[i].plot(close_times, ks[-display_count:], "b", label="k")
        axes[i].plot(close_times, ds[-display_count:], "y", label="d")
        axes[i].plot(close_times, js[-display_count:], "m", label="j")

    # talib
    if args.ADX: # ADX
        name = 'ADX'
        adxs = talib.ADX(klines_df["high"], klines_df["low"], klines_df["close"], timeperiod=14)
        i += 1
        axes[i].set_ylabel(name)
        axes[i].grid(True)
        axes[i].plot(close_times, adxs[-display_count:], "b", label=name)

    if args.ADXR: # ADXR
        name = 'ADXR'
        adxrs = talib.ADXR(klines_df["high"], klines_df["low"], klines_df["close"], timeperiod=14)
        i += 1
        axes[i].set_ylabel(name)
        axes[i].grid(True)
        axes[i].plot(close_times, adxrs[-display_count:], "r", label=name)

    if args.APO: # APO
        name = 'APO'
        real = talib.APO(klines_df["close"], fastperiod=12, slowperiod=26, matype=0)
        i += 1
        axes[i].set_ylabel(name)
        axes[i].grid(True)
        axes[i].plot(close_times, real[-display_count:], "y:", label=name)

    if args.AROON: # AROON
        name = 'AROON'
        aroondown, aroonup = talib.AROON(klines_df["high"], klines_df["low"], timeperiod=14)
        i += 1
        axes[i].set_ylabel(name)
        axes[i].grid(True)
        axes[i].plot(close_times, aroondown[-display_count:], "y:", label=name)
        axes[i].plot(close_times, aroonup[-display_count:], "y:", label=name)

    if args.AROONOSC: # AROONOSC
        name = 'AROONOSC'
        real = talib.AROONOSC(klines_df["high"], klines_df["low"], timeperiod=14)
        i += 1
        axes[i].set_ylabel(name)
        axes[i].grid(True)
        axes[i].plot(close_times, real[-display_count:], "y:", label=name)

    if args.BOP: # BOP
        name = 'BOP'
        real = talib.BOP(klines_df["open"], klines_df["high"], klines_df["low"], klines_df["close"])
        i += 1
        axes[i].set_ylabel(name)
        axes[i].grid(True)
        axes[i].plot(close_times, real[-display_count:], "y:", label=name)

    if args.CCI: # CCI
        name = 'CCI'
        real = talib.CCI(klines_df["high"], klines_df["low"], klines_df["close"], timeperiod=14)
        i += 1
        axes[i].set_ylabel(name)
        axes[i].grid(True)
        axes[i].plot(close_times, real[-display_count:], "y:", label=name)

    if args.CMO: # CMO
        name = 'CMO'
        real = talib.CMO(klines_df["close"], timeperiod=14)
        i += 1
        axes[i].set_ylabel(name)
        axes[i].grid(True)
        axes[i].plot(close_times, real[-display_count:], "y:", label=name)

    if args.DX: # DX
        name = 'DX'
        dxs = talib.DX(klines_df["high"], klines_df["low"], klines_df["close"], timeperiod=14)
        i += 1
        axes[i].set_ylabel(name)
        axes[i].grid(True)
        axes[i].plot(close_times, dxs[-display_count:], "y", label=name)

    if args.MACD: # MACD
        name = 'MACD'
        macd, macdsignal, macdhist = talib.MACD(klines_df["close"], fastperiod=12, slowperiod=26, signalperiod=9)
        i += 1
        axes[i].set_ylabel(name)
        axes[i].grid(True)
        axes[i].plot(close_times, macd[-display_count:], "y", label="dif")
        axes[i].plot(close_times, macdsignal[-display_count:], "b", label="dea")
        axes[i].plot(close_times, macdhist[-display_count:], "r", drawstyle="steps", label="macd")

    if args.MACDEXT: # MACDEXT
        name = 'MACDEXT'
        macd, macdsignal, macdhist = talib.MACDEXT(klines_df["close"],
            fastperiod=12, fastmatype=0, slowperiod=26, slowmatype=0, signalperiod=9, signalmatype=0)
        i += 1
        axes[i].set_ylabel(name)
        axes[i].grid(True)
        axes[i].plot(close_times, macd[-display_count:], "y", label="dif")
        axes[i].plot(close_times, macdsignal[-display_count:], "b", label="dea")
        axes[i].plot(close_times, macdhist[-display_count:], "r", drawstyle="steps", label="macd")

    if args.MACDFIX: # MACDFIX
        name = 'MACDFIX'
        macd, macdsignal, macdhist = talib.MACDFIX(klines_df["close"], signalperiod=9)
        i += 1
        axes[i].set_ylabel(name)
        axes[i].grid(True)
        axes[i].plot(close_times, macd[-display_count:], "y", label="dif")
        axes[i].plot(close_times, macdsignal[-display_count:], "b", label="dea")
        axes[i].plot(close_times, macdhist[-display_count:], "r", drawstyle="steps", label="macd")

    if args.MFI: # 
        name = 'MFI'
        real = talib.MFI(klines_df["high"], klines_df["low"], klines_df["close"], klines_df["volume"])
        i += 1
        axes[i].set_ylabel(name)
        axes[i].grid(True)
        axes[i].plot(close_times, real[-display_count:], "y:", label=name)

    if args.MINUS_DI: # 
        name = 'MINUS_DI'
        real = talib.MINUS_DI(klines_df["high"], klines_df["low"], klines_df["close"], timeperiod=14)
        i += 1
        axes[i].set_ylabel(name)
        axes[i].grid(True)
        axes[i].plot(close_times, real[-display_count:], "y:", label=name)

    if args.MINUS_DM: # 
        name = 'MINUS_DM'
        real = talib.MINUS_DM(klines_df["high"], klines_df["low"], timeperiod=14)
        i += 1
        axes[i].set_ylabel(name)
        axes[i].grid(True)
        axes[i].plot(close_times, real[-display_count:], "y:", label=name)

    if args.MOM: # 
        name = 'MOM'
        real = talib.MOM(klines_df["close"], timeperiod=10)
        i += 1
        axes[i].set_ylabel(name)
        axes[i].grid(True)
        axes[i].plot(close_times, real[-display_count:], "y:", label=name)

    if args.PLUS_DI: # 
        name = 'PLUS_DI'
        real = talib.PLUS_DI(klines_df["high"], klines_df["low"], klines_df["close"], timeperiod=14)
        i += 1
        axes[i].set_ylabel(name)
        axes[i].grid(True)
        axes[i].plot(close_times, real[-display_count:], "y:", label=name)

    if args.PLUS_DM: # 
        name = 'PLUS_DM'
        real = talib.PLUS_DM(klines_df["high"], klines_df["low"], timeperiod=14)
        i += 1
        axes[i].set_ylabel(name)
        axes[i].grid(True)
        axes[i].plot(close_times, real[-display_count:], "y:", label=name)

    if args.PPO: # 
        name = 'PPO'
        real = talib.PPO(klines_df["close"], fastperiod=12, slowperiod=26, matype=0)
        i += 1
        axes[i].set_ylabel(name)
        axes[i].grid(True)
        axes[i].plot(close_times, real[-display_count:], "y:", label=name)

    if args.ROC: # 
        name = 'ROC'
        real = talib.ROC(klines_df["close"], timeperiod=10)
        i += 1
        axes[i].set_ylabel(name)
        axes[i].grid(True)
        axes[i].plot(close_times, real[-display_count:], "y:", label=name)

    if args.ROCP: # 
        name = 'ROCP'
        real = talib.ROCP(klines_df["close"], timeperiod=10)
        i += 1
        axes[i].set_ylabel(name)
        axes[i].grid(True)
        axes[i].plot(close_times, real[-display_count:], "k:", label=name)

    if args.ROCR: # 
        name = 'ROCR'
        real = talib.ROCR(klines_df["close"], timeperiod=10)
        i += 1
        axes[i].set_ylabel(name)
        axes[i].grid(True)
        axes[i].plot(close_times, real[-display_count:], "m:", label=name)

    if args.ROCR100: # 
        name = 'ROCR100'
        real = talib.ROCR100(klines_df["close"], timeperiod=10)
        i += 1
        axes[i].set_ylabel(name)
        axes[i].grid(True)
        axes[i].plot(close_times, real[-display_count:], "b:", label=name)

    if args.RSI is not None: # RSI
        name = 'RSI'
        i += 1
        axes[i].grid(True)

        if len(args.RSI) == 0:
            tps = [14]
        else:
            tps = args.RSI
        cs = ["r", "y", "b"]
        axes[i].set_ylabel("%s%s"%(name, tps))
        for idx, tp in enumerate(tps):
            rsis = talib.RSI(klines_df["close"], timeperiod=tp)
            rsis = [round(a, 3) for a in rsis][-display_count:]
            axes[i].plot(close_times, rsis, cs[idx], label="rsi")

            linetype = "-"
            axes[i].plot(close_times, [90]*len(rsis), linetype, color='g')
            axes[i].plot(close_times, [80]*len(rsis), linetype, color='g')
            axes[i].plot(close_times, [50]*len(rsis), linetype, color='g')
            axes[i].plot(close_times, [40]*len(rsis), linetype, color='g')

            linetype = "--"
            axes[i].plot(close_times, [65]*len(rsis), linetype, color='b')
            axes[i].plot(close_times, [55]*len(rsis), linetype, color='b')
            axes[i].plot(close_times, [30]*len(rsis), linetype, color='b')
            axes[i].plot(close_times, [20]*len(rsis), linetype, color='b')

    if args.STOCH: # STOCH
        name = 'STOCH'
        slowk, slowd = talib.STOCH(klines_df["high"], klines_df["low"], klines_df["close"],
            fastk_period=5, slowk_period=3, slowk_matype=0, slowd_period=3, slowd_matype=0)
        i += 1
        axes[i].set_ylabel(name)
        axes[i].grid(True)
        axes[i].plot(close_times, slowk[-display_count:], "b", label="slowk")
        axes[i].plot(close_times, slowd[-display_count:], "y", label="slowd")

    if args.STOCHF: # 
        name = 'STOCHF'
        fastk, fastd = talib.STOCHF(klines_df["high"], klines_df["low"], klines_df["close"],
            fastk_period=5, fastd_period=3, fastd_matype=0)
        i += 1
        axes[i].set_ylabel(name)
        axes[i].grid(True)
        axes[i].plot(close_times, fastk[-display_count:], "b", label="fastk")
        axes[i].plot(close_times, fastd[-display_count:], "y", label="fastd")

    if args.STOCHRSI: # 
        name = 'STOCHRSI'
        fastk, fastd = talib.STOCHRSI(klines_df["close"],
            timeperiod=14, fastk_period=5, fastd_period=3, fastd_matype=0)
        i += 1
        axes[i].set_ylabel(name)
        axes[i].grid(True)
        axes[i].plot(close_times, fastk[-display_count:], "b", label="fastk")
        axes[i].plot(close_times, fastd[-display_count:], "y", label="fastd")

    if args.TRIX: # 
        name = 'TRIX'
        real = talib.TRIX(klines_df["close"], timeperiod=30)
        i += 1
        axes[i].set_ylabel(name)
        axes[i].grid(True)
        axes[i].plot(close_times, real[-display_count:], "y:", label=name)

    if args.ULTOSC: # 
        name = 'ULTOSC'
        real = talib.ULTOSC(klines_df["high"], klines_df["low"], klines_df["close"], timeperiod1=7, timeperiod2=14, timeperiod3=28)
        i += 1
        axes[i].set_ylabel(name)
        axes[i].grid(True)
        axes[i].plot(close_times, real[-display_count:], "y:", label=name)

    if args.WILLR:
        tp = 14
        name = 'WILLR %s' % tp
        real = talib.WILLR(klines_df["high"], klines_df["low"], klines_df["close"], timeperiod=tp)
        i += 1
        axes[i].set_ylabel(name)
        axes[i].grid(True)
        axes[i].plot(close_times, real[-display_count:], "y:", label=name)

