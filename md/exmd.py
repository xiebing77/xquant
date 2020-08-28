#!/usr/bin/python
"""实盘"""
import time
import datetime
import utils.tools as ts
import common.xquant as xq
import common.kline as kl
from .md import MarketingData


class ExchangeMD(MarketingData):
    """交易所实盘数据"""

    def __init__(self, exchange, kline_data_type=kl.KLINE_DATA_TYPE_JSON):
        super().__init__(exchange.name)

        self.__exchange = exchange
        self.kline_data_type = kline_data_type


    def get_klines(self, symbol, interval, size):
        """ 获取日k线 """
        kls = self.__exchange.get_klines(symbol, interval, size)

        if self.__exchange.kline_data_type == self.kline_data_type:
            return kls
        elif self.__exchange.kline_data_type == kl.KLINE_DATA_TYPE_LIST:
            return kl.trans_from_list_to_json(kls, self.__exchange.kline_column_names)
        else:
            return kl.trans_from_json_to_list(kls, self.__exchange.kline_column_names)

    def get_klines_1day(self, symbol, size):
        """ 获取日k线 """
        return self.get_klines(symbol, kl.KLINE_INTERVAL_1DAY, size)


