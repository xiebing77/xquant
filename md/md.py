#!/usr/bin/python
"""marketing data"""
from exchange.exchange import get_kline_column_names


class MarketingData:
    """市场数据"""

    def __init__(self, exchange):
        self.kline_column_names = get_kline_column_names(exchange)
        for index, value in enumerate(self.kline_column_names):
            if value == "high":
                self.highindex = index
            if value == "low":
                self.lowindex = index
            if value == "open":
                self.openindex = index
            if value == "close":
                self.closeindex = index
            if value == "volume":
                self.volumeindex = index
            if value == "open_time":
                self.opentimeindex = index

    def get_kline_column_names(self):
        return self.kline_column_names
