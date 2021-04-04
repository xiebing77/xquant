#!/usr/bin/python
"""实盘"""
from datetime import datetime
import utils.tools as ts
import common.xquant as xq
import common.kline as kl
from .md import MarketingData


class ExchangeMD(MarketingData):
    """交易所实盘数据"""

    def __init__(self, exchange, kline_data_type=kl.KLINE_DATA_TYPE_JSON):
        super().__init__(exchange, kline_data_type)


    def get_latest_pirce(self, symbol):
        kls = self.get_klines(symbol, kl.KLINE_INTERVAL_1MINUTE, 1)
        if len(kls) <= 0:
            return None, None
        latest_kl = kls[0]
        latest_price = float(latest_kl[self.kline_key_close])
        latest_time  = self.get_kline_close_time(latest_kl)
        return latest_price, latest_time


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


