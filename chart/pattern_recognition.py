#!/usr/bin/python3

import pandas as pd
import talib

import utils.tools as ts
import utils.indicator as ic


def add_argument_pattern_recognition(parser):
    # Pattern Recognition

    # talib
    group = parser.add_argument_group('Pattern Recognition (TaLib)')
    group.add_argument('--CDL2CROWS'         , action="store_true", help='Two Crows')
    group.add_argument('--CDL3BLACKCROWS'    , action="store_true", help='Three Black Crows')
    group.add_argument('--CDL3INSIDE'        , action="store_true", help='Three Inside Up/Down')
    group.add_argument('--CDL3LINESTRIKE'    , action="store_true", help='Three-Line Strike')
    group.add_argument('--CDL3OUTSIDE'       , action="store_true", help='Three Outside Up/Down')
    group.add_argument('--CDL3STARSINSOUTH'  , action="store_true", help='Three Stars In The South')
    group.add_argument('--CDL3WHITESOLDIERS' , action="store_true", help='Three Advancing White Soldiers')


    group.add_argument('--CDLABANDONEDBABY' , action="store_true", help='Abandoned Baby')
    group.add_argument('--CDLADVANCEBLOCK' , action="store_true", help='Advance Block')
    #group.add_argument('--' , action="store_true", help='')

def get_pattern_recognition_count(args):
    count = 0

    if args.CDL2CROWS:
        count += 1
    if args.CDL3BLACKCROWS:
        count += 1
    if args.CDL3INSIDE:
        count += 1
    if args.CDL3LINESTRIKE:
        count += 1
    if args.CDL3OUTSIDE:
        count += 1
    if args.CDL3STARSINSOUTH:
        count += 1
    if args.CDL3WHITESOLDIERS:
        count += 1

    if args.CDLABANDONEDBABY:
        count += 1
    if args.CDLADVANCEBLOCK:
        count += 1
    #if args.:
    #    count += 1
    return count


def handle_pattern_recognition(args, axes, i, klines_df, close_times, display_count):
    # talib
    if args.CDL2CROWS:
        name = 'CDL2CROWS'
        integer = talib.CDL2CROWS(klines_df["open"], klines_df["high"], klines_df["low"], klines_df["close"])
        i += 1
        axes[i].set_ylabel(name)
        axes[i].grid(True)
        axes[i].plot(close_times, integer[-display_count:], "y:", label=name)

    if args.CDL3BLACKCROWS:
        name = 'CDL3BLACKCROWS'
        integer = talib.CDL3BLACKCROWS(klines_df["open"], klines_df["high"], klines_df["low"], klines_df["close"])
        i += 1
        axes[i].set_ylabel(name)
        axes[i].grid(True)
        axes[i].plot(close_times, integer[-display_count:], "y:", label=name)

    if args.CDL3INSIDE:
        name = 'CDL3INSIDE'
        integer = talib.CDL3INSIDE(klines_df["open"], klines_df["high"], klines_df["low"], klines_df["close"])
        i += 1
        axes[i].set_ylabel(name)
        axes[i].grid(True)
        axes[i].plot(close_times, integer[-display_count:], "y:", label=name)

    if args.CDL3LINESTRIKE:
        name = 'CDL3LINESTRIKE'
        integer = talib.CDL3LINESTRIKE(klines_df["open"], klines_df["high"], klines_df["low"], klines_df["close"])
        i += 1
        axes[i].set_ylabel(name)
        axes[i].grid(True)
        axes[i].plot(close_times, integer[-display_count:], "y:", label=name)

    if args.CDL3OUTSIDE:
        name = 'CDL3OUTSIDE'
        integer = talib.CDL3OUTSIDE(klines_df["open"], klines_df["high"], klines_df["low"], klines_df["close"])
        i += 1
        axes[i].set_ylabel(name)
        axes[i].grid(True)
        axes[i].plot(close_times, integer[-display_count:], "y:", label=name)

    if args.CDL3STARSINSOUTH:
        name = 'CDL3STARSINSOUTH'
        integer = talib.CDL3STARSINSOUTH(klines_df["open"], klines_df["high"], klines_df["low"], klines_df["close"])
        i += 1
        axes[i].set_ylabel(name)
        axes[i].grid(True)
        axes[i].plot(close_times, integer[-display_count:], "y:", label=name)

    if args.CDL3WHITESOLDIERS:
        name = 'CDL3WHITESOLDIERS'
        integer = talib.CDL3WHITESOLDIERS(klines_df["open"], klines_df["high"], klines_df["low"], klines_df["close"])
        i += 1
        axes[i].set_ylabel(name)
        axes[i].grid(True)
        axes[i].plot(close_times, integer[-display_count:], "y:", label=name)

    if args.CDLABANDONEDBABY:
        name = 'CDLABANDONEDBABY'
        integer = talib.CDLABANDONEDBABY(klines_df["open"], klines_df["high"], klines_df["low"], klines_df["close"])
        i += 1
        axes[i].set_ylabel(name)
        axes[i].grid(True)
        axes[i].plot(close_times, integer[-display_count:], "y:", label=name)

    if args.CDLADVANCEBLOCK:
        name = 'CDLADVANCEBLOCK'
        integer = talib.CDLADVANCEBLOCK(klines_df["open"], klines_df["high"], klines_df["low"], klines_df["close"])
        i += 1
        axes[i].set_ylabel(name)
        axes[i].grid(True)
        axes[i].plot(close_times, integer[-display_count:], "y:", label=name)

    '''
    if args.:
        name = ''
        integer = talib.(klines_df["open"], klines_df["high"], klines_df["low"], klines_df["close"])
        i += 1
        axes[i].set_ylabel(name)
        axes[i].grid(True)
        axes[i].plot(close_times, integer[-display_count:], "y:", label=name)
    '''

