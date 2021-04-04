#!/usr/bin/python
"""marketing data"""
from datetime import datetime, timedelta
import common.kline as kl
import exchange.exchange  as ex


class MarketingData:
    """市场数据"""

    def __init__(self, exchange, kline_data_type):
        self.kline_column_names   = exchange.kline_column_names
        self.kline_key_open_time  = exchange.kline_key_open_time
        self.kline_key_close_time = exchange.kline_key_close_time
        self.kline_key_open       = exchange.kline_key_open
        self.kline_key_close      = exchange.kline_key_close
        self.kline_key_high       = exchange.kline_key_high
        self.kline_key_low        = exchange.kline_key_low
        self.kline_key_volume     = exchange.kline_key_volume

        self._exchange = exchange
        self.kline_data_type = kline_data_type


    def get_kline_column_names(self):
        return self._exchange.kline_column_names

    def get_kline_seat_open_time(self):
        if self.kline_data_type == kl.KLINE_DATA_TYPE_LIST:
            return self._exchange.kline_idx_open_time
        else:
            return self._exchange.kline_key_open_time

    def get_kline_seat_close_time(self):
        if self.kline_data_type == kl.KLINE_DATA_TYPE_LIST:
            return self._exchange.kline_idx_close_time
        else:
            return self._exchange.kline_key_close_time

    def get_kline_seat_open(self):
        if self.kline_data_type == kl.KLINE_DATA_TYPE_LIST:
            return self._exchange.kline_idx_open
        else:
            return self._exchange.kline_key_open

    def get_kline_seat_close(self):
        if self.kline_data_type == kl.KLINE_DATA_TYPE_LIST:
            return self._exchange.kline_idx_close
        else:
            return self._exchange.kline_key_close

    def get_kline_seat_high(self):
        if self.kline_data_type == kl.KLINE_DATA_TYPE_LIST:
            return self._exchange.kline_idx_high
        else:
            return self._exchange.kline_key_high

    def get_kline_seat_low(self):
        if self.kline_data_type == kl.KLINE_DATA_TYPE_LIST:
            return self._exchange.kline_idx_low
        else:
            return self._exchange.kline_key_low

    def get_kline_seat_volume(self):
        if self.kline_data_type == kl.KLINE_DATA_TYPE_LIST:
            return self._exchange.kline_idx_volume
        else:
            return self._exchange.kline_key_volume


    def get_kline_open_time(self, kl):
        return datetime.fromtimestamp(kl[self.get_kline_seat_open_time()]/1000)

    def get_kline_close_time(self, kl):
        return datetime.fromtimestamp(kl[self.get_kline_seat_close_time()]/1000)

