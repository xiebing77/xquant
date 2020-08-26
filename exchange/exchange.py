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
        return BinanceExchange.kline_column_names
    elif exchange_name == BINANCE_MARGIN_EXCHANGE_NAME:
        return BinanceMargin.kline_column_names
    elif exchange_name == OKEX_SPOT_EXCHANGE_NAME:
        return OkexExchange.kline_column_names
    else:
        return None

# key
def get_kline_key_open_time(exchange_name):
    if exchange_name == BINANCE_SPOT_EXCHANGE_NAME:
        return BinanceExchange.kline_key_open_time
    elif exchange_name == BINANCE_MARGIN_EXCHANGE_NAME:
        return BinanceMargin.kline_key_open_time
    else:
        return None

def get_kline_key_close_time(exchange_name):
    if exchange_name == BINANCE_SPOT_EXCHANGE_NAME:
        return BinanceExchange.kline_key_close_time
    elif exchange_name == BINANCE_MARGIN_EXCHANGE_NAME:
        return BinanceMargin.kline_key_close_time
    else:
        return None

def get_kline_key_open(exchange_name):
    if exchange_name == BINANCE_SPOT_EXCHANGE_NAME:
        return BinanceExchange.kline_key_open
    elif exchange_name == BINANCE_MARGIN_EXCHANGE_NAME:
        return BinanceMargin.kline_key_open
    else:
        return None

def get_kline_key_close(exchange_name):
    if exchange_name == BINANCE_SPOT_EXCHANGE_NAME:
        return BinanceExchange.kline_key_close
    elif exchange_name == BINANCE_MARGIN_EXCHANGE_NAME:
        return BinanceMargin.kline_key_close
    else:
        return None

def get_kline_key_high(exchange_name):
    if exchange_name == BINANCE_SPOT_EXCHANGE_NAME:
        return BinanceExchange.kline_key_high
    elif exchange_name == BINANCE_MARGIN_EXCHANGE_NAME:
        return BinanceMargin.kline_key_high
    else:
        return None

def get_kline_key_low(exchange_name):
    if exchange_name == BINANCE_SPOT_EXCHANGE_NAME:
        return BinanceExchange.kline_key_low
    elif exchange_name == BINANCE_MARGIN_EXCHANGE_NAME:
        return BinanceMargin.kline_key_low
    else:
        return None

def get_kline_key_volume(exchange_name):
    if exchange_name == BINANCE_SPOT_EXCHANGE_NAME:
        return BinanceExchange.kline_key_volume
    elif exchange_name == BINANCE_MARGIN_EXCHANGE_NAME:
        return BinanceMargin.kline_key_volume
    else:
        return None

# idx
def get_kline_idx_open_time(exchange_name):
    if exchange_name == BINANCE_SPOT_EXCHANGE_NAME:
        return BinanceExchange.kline_idx_open_time
    elif exchange_name == BINANCE_MARGIN_EXCHANGE_NAME:
        return BinanceMargin.kline_idx_open_time
    else:
        return None

def get_kline_idx_close_time(exchange_name):
    if exchange_name == BINANCE_SPOT_EXCHANGE_NAME:
        return BinanceExchange.kline_idx_close_time
    elif exchange_name == BINANCE_MARGIN_EXCHANGE_NAME:
        return BinanceMargin.kline_idx_close_time
    else:
        return None

def get_kline_idx_open(exchange_name):
    if exchange_name == BINANCE_SPOT_EXCHANGE_NAME:
        return BinanceExchange.kline_idx_open
    elif exchange_name == BINANCE_MARGIN_EXCHANGE_NAME:
        return BinanceMargin.kline_idx_open
    else:
        return None

def get_kline_idx_close(exchange_name):
    if exchange_name == BINANCE_SPOT_EXCHANGE_NAME:
        return BinanceExchange.kline_idx_close
    elif exchange_name == BINANCE_MARGIN_EXCHANGE_NAME:
        return BinanceMargin.kline_idx_close
    else:
        return None

def get_kline_idx_high(exchange_name):
    if exchange_name == BINANCE_SPOT_EXCHANGE_NAME:
        return BinanceExchange.kline_idx_high
    elif exchange_name == BINANCE_MARGIN_EXCHANGE_NAME:
        return BinanceMargin.kline_idx_high
    else:
        return None

def get_kline_idx_low(exchange_name):
    if exchange_name == BINANCE_SPOT_EXCHANGE_NAME:
        return BinanceExchange.kline_idx_low
    elif exchange_name == BINANCE_MARGIN_EXCHANGE_NAME:
        return BinanceMargin.kline_idx_low
    else:
        return None

def get_kline_idx_volume(exchange_name):
    if exchange_name == BINANCE_SPOT_EXCHANGE_NAME:
        return BinanceExchange.kline_idx_volume
    elif exchange_name == BINANCE_MARGIN_EXCHANGE_NAME:
        return BinanceMargin.kline_idx_volume
    else:
        return None

