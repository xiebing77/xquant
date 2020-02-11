#!/usr/bin/python
"""运行环境引擎"""
import matplotlib.pyplot as plt
import matplotlib.dates as dts
from matplotlib import gridspec
import mpl_finance as mpf
import pandas as pd
import talib
from datetime import datetime,timedelta
import common.log as log
import utils.tools as ts
import utils.indicator as ic
import common.xquant as xq
import db.mongodb as md
from exchange.binanceExchange import BinanceExchange
from exchange.okexExchange import OkexExchange


class MarketingData:
    """市场数据"""

    def __init__(self, exchange):
        if exchange == "binance":
            self.kline_column_names = BinanceExchange.get_kline_column_names()
        elif exchange == "okex":
            self.kline_column_names = OkexExchange.get_kline_column_names()

    def get_kline_column_names(self):
        return self.kline_column_names
