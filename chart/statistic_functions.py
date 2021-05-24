#!/usr/bin/python3

import pandas as pd
import talib

import utils.tools as ts
import utils.indicator as ic


def add_argument_statistic_functions(parser):
    # Statistic Functions

    # talib
    group = parser.add_argument_group('Volatility Indicators (TaLib)')
    group.add_argument('--BETA', action="store_true", help='Beta')
    group.add_argument('--CORREL', action="store_true", help='Pearson’s Correlation Coefficient (r)')
    group.add_argument('--LINEARREG', action="store_true", help='Linear Regression')
    group.add_argument('--LINEARREG_ANGLE', action="store_true", help='Linear Regression Angle')
    group.add_argument('--LINEARREG_INTERCEPT', action="store_true", help='Linear Regression Intercept')
    group.add_argument('--LINEARREG_SLOPE', action="store_true", help='Linear Regression Slope')
    group.add_argument('--STDDEV', action="store_true", help='Standard Deviation')
    group.add_argument('--VAR', action="store_true", help='VAR')


def get_statistic_functions_count(args):
    count = 0

    if args.BETA:
        count += 1
    if args.CORREL:
        count += 1
    if args.LINEARREG:
        count += 1
    if args.LINEARREG_ANGLE:
        count += 1
    if args.LINEARREG_INTERCEPT:
        count += 1
    if args.LINEARREG_SLOPE:
        count += 1
    if args.STDDEV:
        count += 1
    if args.VAR:
        count += 1

    return count


def handle_statistic_functions(args, axes, i, klines_df, close_times, display_count):
    # talib
    if args.BETA:
        name = 'BETA'
        real = talib.BETA(klines_df["high"], klines_df["low"], timeperiod=5)
        i += 1
        axes[i].set_ylabel(name)
        axes[i].grid(True)
        axes[i].plot(close_times, real[-display_count:], "y:", label=name)

    if args.CORREL:
        name = 'CORREL'
        real = talib.CORREL(klines_df["high"], klines_df["low"], timeperiod=30)
        i += 1
        axes[i].set_ylabel(name)
        axes[i].grid(True)
        axes[i].plot(close_times, real[-display_count:], "y:", label=name)

    if args.LINEARREG:
        name = 'LINEARREG'
        real = talib.LINEARREG(klines_df["close"], timeperiod=14)
        i += 1
        axes[i].set_ylabel(name)
        axes[i].grid(True)
        axes[i].plot(close_times, real[-display_count:], "y:", label=name)

    if args.LINEARREG_ANGLE:
        name = 'LINEARREG_ANGLE'
        real = talib.LINEARREG_ANGLE(klines_df["close"], timeperiod=14)
        i += 1
        axes[i].set_ylabel(name)
        axes[i].grid(True)
        axes[i].plot(close_times, real[-display_count:], "y:", label=name)

    if args.LINEARREG_INTERCEPT:
        name = 'LINEARREG_INTERCEPT'
        real = talib.LINEARREG_INTERCEPT(klines_df["close"], timeperiod=14)
        i += 1
        axes[i].set_ylabel(name)
        axes[i].grid(True)
        axes[i].plot(close_times, real[-display_count:], "y:", label=name)

    if args.LINEARREG_SLOPE:
        name = 'LINEARREG_SLOPE'
        real = talib.LINEARREG_SLOPE(klines_df["close"], timeperiod=14)
        i += 1
        axes[i].set_ylabel(name)
        axes[i].grid(True)
        axes[i].plot(close_times, real[-display_count:], "y:", label=name)

    if args.STDDEV:
        name = 'STDDEV'
        real = talib.STDDEV(klines_df["close"], timeperiod=5, nbdev=1)
        i += 1
        axes[i].set_ylabel(name)
        axes[i].grid(True)
        axes[i].plot(close_times, real[-display_count:], "y:", label=name)

    if args.VAR:
        name = 'VAR'
        real = talib.VAR(klines_df["close"], timeperiod=5, nbdev=1)
        i += 1
        axes[i].set_ylabel(name)
        axes[i].grid(True)
        axes[i].plot(close_times, real[-display_count:], "y:", label=name)



