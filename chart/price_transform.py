#!/usr/bin/python3
import talib


def add_argument_price_transform(parser):
    # talib
    group = parser.add_argument_group('Price Transform (TaLib)')
    group.add_argument('--AVGPRICE', action="store_true", help='Average Price')
    group.add_argument('--MEDPRICE', action="store_true", help='Median Price')
    group.add_argument('--TYPPRICE', action="store_true", help='Typical Price')
    group.add_argument('--WCLPRICE', action="store_true", help='Weighted Close Price')

def handle_price_transform(args, kax, klines_df, close_times, display_count):

    os_key = 'AVGPRICE'
    if args.AVGPRICE:
        real = talib.AVGPRICE(klines_df["open"], klines_df["high"], klines_df["low"], klines_df["close"])
        kax.plot(close_times, real[-display_count:], "y", label=os_key)

    os_key = 'MEDPRICE'
    if args.MEDPRICE:
        real = talib.MEDPRICE(klines_df["high"], klines_df["low"])
        kax.plot(close_times, real[-display_count:], "y", label=os_key)

    os_key = 'TYPPRICE'
    if args.TYPPRICE:
        real = talib.TYPPRICE(klines_df["high"], klines_df["low"], klines_df["close"])
        kax.plot(close_times, real[-display_count:], "y", label=os_key)

    os_key = 'WCLPRICE'
    if args.WCLPRICE:
        real = talib.WCLPRICE(klines_df["high"], klines_df["low"], klines_df["close"])
        kax.plot(close_times, real[-display_count:], "y", label=os_key)

