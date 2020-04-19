#!/usr/bin/python
"""交易所"""

from exchange.binanceExchange import BinanceExchange
from exchange.binanceMargin import BinanceMargin
from exchange.okexExchange import OkexExchange

BINANCE_SPOT_EXCHANGE_NAME = 'binance'
BINANCE_MARGIN_EXCHANGE_NAME = 'binance_margin'

OKEX_SPOT_EXCHANGE_NAME = 'okex'

exchange_names = [BINANCE_SPOT_EXCHANGE_NAME, BINANCE_MARGIN_EXCHANGE_NAME, OKEX_SPOT_EXCHANGE_NAME]

def create_exchange(exchange_name):
    if exchange_name == BINANCE_SPOT_EXCHANGE_NAME:
        return BinanceExchange(debug=True)
    elif exchange_name == BINANCE_MARGIN_EXCHANGE_NAME:
        return BinanceMargin(debug=True)
    elif exchange_name == OKEX_SPOT_EXCHANGE_NAME:
        return OkexExchange(debug=True)
    else:
        return None

def get_kline_column_names(exchange_name):
    if exchange_name == BINANCE_SPOT_EXCHANGE_NAME:
        return BinanceExchange.get_kline_column_names()
    elif exchange_name == BINANCE_MARGIN_EXCHANGE_NAME:
        return BinanceMargin.get_kline_column_names()
    elif exchange_name == OKEX_SPOT_EXCHANGE_NAME:
        return OkexExchange.get_kline_column_names()
    else:
        return None
