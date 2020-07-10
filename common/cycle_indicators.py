#!/usr/bin/python3

import pandas as pd
import talib

import utils.tools as ts
import utils.indicator as ic


def add_argument_cycle_indicators(parser):

    # talib
    group = parser.add_argument_group('Cycle Indicators (TaLib)')
    group.add_argument('--HT_DCPERIOD' , action="store_true", help='Hilbert Transform - Dominant Cycle Period')
    group.add_argument('--HT_DCPHASE'  , action="store_true", help='Hilbert Transform - Dominant Cycle Phase')
    group.add_argument('--HT_PHASOR'   , action="store_true", help='Hilbert Transform - Phasor Components')
    group.add_argument('--HT_SINE'     , action="store_true", help='Hilbert Transform - SineWave')
    group.add_argument('--HT_TRENDMODE', action="store_true", help='Hilbert Transform - Trend vs Cycle Mode')


def get_cycle_indicators_count(args):
    count = 0

    if args.HT_DCPERIOD:
        count += 1
    if args.HT_DCPHASE:
        count += 1
    if args.HT_PHASOR:
        count += 1
    if args.HT_SINE:
        count += 1
    if args.HT_TRENDMODE:
        count += 1

    return count


def handle_cycle_indicators(args, axes, i, klines_df, close_times, display_count):
    # talib
    if args.HT_DCPERIOD:
        name = 'HT_DCPERIOD'
        real = talib.HT_DCPERIOD(klines_df["close"])
        i += 1
        axes[i].set_ylabel(name)
        axes[i].grid(True)
        axes[i].plot(close_times, real[-display_count:], "y:", label=name)

    if args.HT_DCPHASE:
        name = 'HT_DCPHASE'
        real = talib.HT_DCPHASE(klines_df["close"])
        i += 1
        axes[i].set_ylabel(name)
        axes[i].grid(True)
        axes[i].plot(close_times, real[-display_count:], "y:", label=name)

    if args.HT_PHASOR:
        name = 'HT_PHASOR'
        real = talib.HT_PHASOR(klines_df["close"])
        i += 1
        axes[i].set_ylabel(name)
        axes[i].grid(True)
        axes[i].plot(close_times, real[-display_count:], "y:", label=name)

    if args.HT_SINE:
        name = 'HT_SINE'
        real = talib.HT_SINE(klines_df["close"])
        i += 1
        axes[i].set_ylabel(name)
        axes[i].grid(True)
        axes[i].plot(close_times, real[-display_count:], "y:", label=name)

    if args.HT_TRENDMODE:
        name = 'HT_TRENDMODE'
        real = talib.HT_TRENDMODE(klines_df["close"])
        i += 1
        axes[i].set_ylabel(name)
        axes[i].grid(True)
        axes[i].plot(close_times, real[-display_count:], "y:", label=name)


