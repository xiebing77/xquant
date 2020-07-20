#!/usr/bin/python3

import pandas as pd
import talib

import utils.tools as ts
import utils.indicator as ic


def add_argument_volatility_indicators(parser):
    # Volume Indicators

    # talib
    group = parser.add_argument_group('Volatility Indicators (TaLib)')
    group.add_argument('--ATR'   , action="store_true", help='Average True Range')
    group.add_argument('--NATR'  , action="store_true", help='Normalized Average True Range')
    group.add_argument('--TRANGE', action="store_true", help='On Balance Volume')


def get_volatility_indicators_count(args):
    count = 0

    if args.ATR:
        count += 1
    if args.NATR:
        count += 1
    if args.TRANGE:
        count += 1

    return count


def handle_volatility_indicators(args, axes, i, klines_df, close_times, display_count):
    # talib
    if args.ATR:
        name = 'ATR'
        real = talib.ATR(klines_df["high"], klines_df["low"], klines_df["close"], timeperiod=14)
        i += 1
        axes[i].set_ylabel(name)
        axes[i].grid(True)
        axes[i].plot(close_times, real[-display_count:], "y:", label=name)

    if args.NATR:
        name = 'NATR'
        real = talib.NATR(klines_df["high"], klines_df["low"], klines_df["close"], timeperiod=14)
        i += 1
        axes[i].set_ylabel(name)
        axes[i].grid(True)
        axes[i].plot(close_times, real[-display_count:], "y:", label=name)

    if args.TRANGE:
        name = 'TRANGE'
        real = talib.TRANGE(klines_df["high"], klines_df["low"], klines_df["close"])
        i += 1
        axes[i].set_ylabel(name)
        axes[i].grid(True)
        axes[i].plot(close_times, real[-display_count:], "y:", label=name)



