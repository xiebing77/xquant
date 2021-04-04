#!/usr/bin/python
"""交易所"""

from exchange.binanceExchange import BinanceExchange
from exchange.binanceMargin import BinanceMargin
from exchange.binanceFuture import BinanceFuture
from exchange.okexExchange import OkexExchange
from exchange.kuaiqiBroker import KuaiqiBroker

BINANCE_SPOT_EXCHANGE_NAME = 'binance'
BINANCE_MARGIN_EXCHANGE_NAME = 'binance_margin'
BINANCE_FUTURE_EXCHANGE_NAME = 'binance_future'

OKEX_SPOT_EXCHANGE_NAME = 'okex'

KUAIQI_EXCHANGE_NAME = 'kuaiqi'

exchange_names = [BINANCE_SPOT_EXCHANGE_NAME, BINANCE_MARGIN_EXCHANGE_NAME, BINANCE_FUTURE_EXCHANGE_NAME, OKEX_SPOT_EXCHANGE_NAME, KUAIQI_EXCHANGE_NAME]

def create_exchange(exchange_name):
    if exchange_name == BINANCE_SPOT_EXCHANGE_NAME:
        return BinanceExchange(debug=True)
    elif exchange_name == BINANCE_MARGIN_EXCHANGE_NAME:
        return BinanceMargin(debug=True)
    elif exchange_name == BINANCE_FUTURE_EXCHANGE_NAME:
        return BinanceFuture(debug=True)
    elif exchange_name == OKEX_SPOT_EXCHANGE_NAME:
        return OkexExchange(debug=True)
    elif exchange_name == KUAIQI_EXCHANGE_NAME:
        return KuaiqiBroker(debug=True)
    else:
        return None

