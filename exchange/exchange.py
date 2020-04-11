#!/usr/bin/python
"""交易所"""

from exchange.binanceExchange import BinanceExchange
from exchange.binanceMargin import BinanceMargin
from exchange.okexExchange import OkexExchange


def create_exchange(exchange_name):
    if exchange_name == "binance":
        return BinanceExchange(debug=True)
    elif exchange_name == "binance_margin":
        return BinanceMargin(debug=True)
    elif exchange_name == "okex":
        return OkexExchange(debug=True)
    else:
        return None


def get_kline_column_names(exchange_name):
    if exchange_name == "binance":
        return BinanceExchange.get_kline_column_names()
    elif exchange_name == "binance_margin":
        return BinanceMargin.get_kline_column_names()
    elif exchange_name == "okex":
        return OkexExchange.get_kline_column_names()
    else:
        return None
