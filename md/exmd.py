#!/usr/bin/python
"""实盘"""
import time
import datetime
import utils.tools as ts
import common.xquant as xq
from .md import MarketingData


class ExchangeMD(MarketingData):
    """交易所实盘数据"""

    def __init__(self, exchange):
        super().__init__(exchange.name)

        self.__exchange = exchange

    def get_klines(self, symbol, interval, size):
        """ 获取日k线 """
        return self.__exchange.get_klines(symbol, interval, size)

    def get_klines_1day(self, symbol, size):
        """ 获取日k线 """
        return self.__exchange.get_klines_1day(symbol, size)


