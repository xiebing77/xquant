#!/usr/bin/python
"""交易所"""

from exchange.binanceExchange import BinanceExchange
from exchange.binanceMargin import BinanceMargin
from exchange.binanceFuture import BinanceFuture
from exchange.okexExchange import OkexExchange
from exchange.kuaiqiBroker import KuaiqiBroker


exchangeClasses = [BinanceExchange, BinanceMargin, BinanceFuture, OkexExchange, KuaiqiBroker]


def get_exchange_names():
    return [ ec.name for ec in exchangeClasses]


def create_exchange(exchange_name):
    for ec in exchangeClasses:
        if ec.name == exchange_name:
            return ec(debug=True)
    return None

