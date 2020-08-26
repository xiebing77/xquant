#!/usr/bin/python
"""marketing data"""
import common.kline as kl
import exchange.exchange  as ex


class MarketingData:
    """市场数据"""

    def __init__(self, exchange_name):
        self.exchange_name = exchange_name
        self.kline_column_names = ex.get_kline_column_names(exchange_name)

        self.kline_key_open_time  = ex.get_kline_key_open_time(exchange_name)
        self.kline_key_close_time = ex.get_kline_key_close_time(exchange_name)
        self.kline_key_open       = ex.get_kline_key_open(exchange_name)
        self.kline_key_close      = ex.get_kline_key_close(exchange_name)
        self.kline_key_high       = ex.get_kline_key_high(exchange_name)
        self.kline_key_low        = ex.get_kline_key_low(exchange_name)
        self.kline_key_volume     = ex.get_kline_key_volume(exchange_name)

    def get_kline_column_names(self):
        return self.kline_column_names

    def get_kline_seat_open_time(self):
        if self.kline_data_type == kl.KLINE_DATA_TYPE_LIST:
            return ex.get_kline_idx_open_time(self.exchange_name)
        else:
            return ex.get_kline_key_open_time(self.exchange_name)

    def get_kline_seat_close_time(self):
        if self.kline_data_type == kl.KLINE_DATA_TYPE_LIST:
            return ex.get_kline_idx_close_time(self.exchange_name)
        else:
            return ex.get_kline_key_close_time(self.exchange_name)

    def get_kline_seat_open(self):
        if self.kline_data_type == kl.KLINE_DATA_TYPE_LIST:
            return ex.get_kline_idx_open(self.exchange_name)
        else:
            return ex.get_kline_key_open(self.exchange_name)

    def get_kline_seat_close(self):
        if self.kline_data_type == kl.KLINE_DATA_TYPE_LIST:
            return ex.get_kline_idx_close(self.exchange_name)
        else:
            return ex.get_kline_key_close(self.exchange_name)

    def get_kline_seat_high(self):
        if self.kline_data_type == kl.KLINE_DATA_TYPE_LIST:
            return ex.get_kline_idx_high(self.exchange_name)
        else:
            return ex.get_kline_key_high(self.exchange_name)

    def get_kline_seat_low(self):
        if self.kline_data_type == kl.KLINE_DATA_TYPE_LIST:
            return ex.get_kline_idx_low(self.exchange_name)
        else:
            return ex.get_kline_key_low(self.exchange_name)

    def get_kline_seat_volume(self):
        if self.kline_data_type == kl.KLINE_DATA_TYPE_LIST:
            return ex.get_kline_idx_volume(self.exchange_name)
        else:
            return ex.get_kline_key_volume(self.exchange_name)
