#!/usr/bin/python3

import pandas as pd
import talib

import utils.indicator as ic


def add_argument_other_indicators(parser):
    # other Indicators

    group = parser.add_argument_group('Other Indicators')
    group.add_argument('--nBIAS', type=int, nargs='*', help='Bias Ratio: close/ma - 1')
    group.add_argument('--nmBIAS', type=int, nargs='*', help='Bias Ratio: nBIAS - mBIAS')
    group.add_argument('--BIAS', type=int, nargs='*', help='Bias Ratio: ma_short/ma_long - 1')


def get_other_indicators_count(args):
    count = 0

    if args.nBIAS is not None:
        count += 1
    if args.nmBIAS is not None:
        count += 1
    if args.BIAS is not None:
        count += 1

    return count


def handle_other_indicators(args, axes, i, klines_df, close_times, display_count):
    if args.nBIAS is not None:
        name = 'nBIAS'
        i += 1
        axes[i].grid(True)

        if len(args.nBIAS) == 0:
            tps = [55]
        else:
            tps = args.nBIAS
        cs = ["r", "y", "b", "m"]
        axes[i].set_ylabel("%s%s"%(name, tps))
        for idx, tp in enumerate(tps):
            ta_emas = talib.EMA(klines_df["close"], tp)
            real = ic.pd_biases(pd.to_numeric(klines_df["close"]), ta_emas)
            axes[i].plot(close_times, real[-display_count:], cs[idx%len(cs)], label=tp)

    if args.nmBIAS is not None:
        name = 'nmBIAS'
        i += 1
        axes[i].grid(True)

        if len(args.nmBIAS) == 0:
            tps = [13, 55]
        else:
            tps = args.nBIAS
        cs = ["r", "y", "b", "m"]
        axes[i].set_ylabel("%s%s"%(name, tps))

        closes = pd.to_numeric(klines_df["close"])
        emas_s = talib.EMA(closes, tps[0])
        emas_l = talib.EMA(closes, tps[1])
        real = ic.pd_biases(closes, emas_s) - ic.pd_biases(closes, emas_l)
        axes[i].plot(close_times, real[-display_count:], cs[0], label=tps)

    if args.BIAS is not None:
        name = 'BIAS'
        i += 1
        axes[i].grid(True)

        if len(args.BIAS) == 0:
            tps = [13, 55]
        else:
            tps = args.BIAS
        cs = ["r", "y", "b", "m"]
        axes[i].set_ylabel("%s%s"%(name, tps))
        idx = 0
        while idx < len(tps)-1:
            emas_s = talib.EMA(klines_df["close"], tps[idx])
            emas_l = talib.EMA(klines_df["close"], tps[idx+1])
            real = ic.pd_biases(emas_s, emas_l)
            axes[i].plot(close_times, real[-display_count:], cs[idx%len(cs)], label="%d-%d"%(tps[idx], tps[idx+1]))
            idx += 2


