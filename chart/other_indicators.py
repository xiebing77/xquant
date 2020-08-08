#!/usr/bin/python3

import pandas as pd
import talib

import utils.indicator as ic


def add_argument_other_indicators(parser):
    # other Indicators

    group = parser.add_argument_group('Other Indicators')
    group.add_argument('--nBIAS', type=int, nargs='*', help='Bias Ratio')


def get_other_indicators_count(args):
    count = 0

    if args.nBIAS is not None:
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



