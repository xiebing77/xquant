#!/usr/bin/python
"""回测环境"""
import sys
from datetime import datetime, timedelta, time
import uuid
import utils.tools as ts
import common.xquant as xq
import common.kline as kl
from db.mongodb import get_mongodb
import exchange.exchange as ex
from .md import MarketingData


class DBMD(MarketingData):
    """来源于本地数据库的市场数据"""

    def __init__(self, exchange_name, kline_data_type=kl.KLINE_DATA_TYPE_JSON):
        exchange = ex.create_exchange(exchange_name)
        super().__init__(exchange, kline_data_type)

        self.md_db = get_mongodb(exchange.name)

        self.tick_time = None

        self.k1ms_cache = {}
        self.k1ms_cache_s_time = {}

        '''
        self.k1ds_cache = None
        self.k1ds_cache_s_time = None
        self.k1ds_cache_e_time = None
        '''

        self.klines_cache = {}

    def get_latest_pirce(self, symbol):
        collection = kl.get_kline_collection(symbol, kl.KLINE_INTERVAL_1MINUTE)
        klines = self.md_db.find_sort(collection, {}, self.kline_key_open_time, -1, 1)
        if len(klines) <= 0:
            return None, None
        latest_kl = klines[0]
        latest_price = float(latest_kl[self.kline_key_close])
        latest_time = self.get_kline_close_time(latest_kl)
        return latest_price, latest_time


    def get_oldest_time(self, symbol, kline_type):
        collection = kl.get_kline_collection(symbol, kline_type)
        klines = self.md_db.find_sort(collection, {}, self.kline_key_open_time, 1, 1)
        if len(klines) <= 0:
            return None
        return self.get_kline_open_time(klines[0])

    def get_latest_time(self, symbol, kline_type):
        collection = kl.get_kline_collection(symbol, kline_type)
        interval = timedelta(seconds=kl.get_interval_seconds(kline_type))
        klines = self.md_db.find_sort(collection, {}, self.kline_key_open_time, -1, 1)
        if len(klines) <= 0:
            return None
        return (self.get_kline_open_time(klines[0]) + interval)

    def get_original_klines(self, collection, s_time, e_time):
        """ 获取k线 """
        ks = self.md_db.find(
            collection,
            {
                self.kline_key_open_time: {
                    "$gte": self.get_data_ts_from_time(s_time),
                    "$lt": self.get_data_ts_from_time(e_time),
                }
            },
            {"_id":0},
        )
        return ks

    def __get_klines_1min(self, symbol, s_time, e_time):
        """ 获取分钟k线 """
        return self.get_original_klines(kl.get_kline_collection(symbol, kl.KLINE_INTERVAL_1MINUTE), s_time, e_time)

    '''
    def __get_klines_1day(self, symbol, s_time, e_time):
        """ 获取日k线 """
        return self.get_original_klines(kl.get_kline_collection(symbol, kl.KLINE_INTERVAL_1DAY), s_time, e_time)
    '''

    def __get_klines_cache(self, symbol, interval, s_time, e_time):
        """ 获取k线缓存 """
        if (
            interval not in self.klines_cache
            or s_time != self.klines_cache[interval]["s_time"]
            or e_time != self.klines_cache[interval]["e_time"]
        ):
            cache = {}
            cache["data"] = self.get_original_klines(kl.get_kline_collection(symbol, interval), s_time, e_time)
            cache["s_time"] = s_time
            cache["e_time"] = e_time
            self.klines_cache[interval] = cache

        return self.klines_cache[interval]["data"]

    def __join_klines(self, symbol, interval, size, since=None):
        """ 拼接k线 """
        # print("tick_time     : ", self.tick_time)
        tick_open_time = kl.get_open_time(interval, self.tick_time)
        td = kl.get_timedelta(interval, size)
        #print("tick_open_time: ", tick_open_time)

        if since is None:
            # 取出之前的k线
            s_time = tick_open_time - td
            e_time = tick_open_time
        else:
            s_time = kl.get_open_time(interval, since)
            e_time = s_time + td
            #print("%s~%s"%(s_time, e_time))

        ks = self.__get_klines_cache(symbol, interval, s_time, e_time)

        k = self.__create_kline_from_1min(
            symbol, interval, tick_open_time, self.tick_time
        )

        return ks + k

    def get_json_klines(self, symbol, interval, size, since=None):
        if interval == kl.KLINE_INTERVAL_1MINUTE:
            klines = self.get_klines_1min(symbol, interval, size, since)
        else:
            klines = self.__join_klines(symbol, interval, size, since)
        return klines

    def get_klines(self, symbol, interval, size, since=None):
        klines = self.get_json_klines(symbol, interval, size, since)
        if self.kline_data_type == kl.KLINE_DATA_TYPE_LIST:
            return kl.trans_from_json_to_list(klines, self.kline_column_names)
        else:
            return klines

    def get_klines_1min(self, symbol, interval, size, since=None):
        """ 获取分钟k线 """
        if since is None:
            s_time = self.tick_time - timedelta(minutes=size)
            e_time = self.tick_time
        else:
            s_time = since
            e_time = since + timedelta(minutes=size)

        # print("1min s_time:",s_time)
        # print("1min e_time:",e_time)
        # print("1min s_time timestamp: ",s_time.timestamp())
        # print("1min e_time timestamp: ",e_time.timestamp())

        k1ms = self.__get_klines_1min_cache(symbol, interval, s_time, e_time)
        return k1ms

    def __get_klines_1min_cache(self, symbol, interval, s_time, e_time):
        """ 获取分钟k线 """
        if interval in self.k1ms_cache:
            if self.k1ms_cache[interval][0][self.kline_key_open_time] == self.get_data_ts_from_time(s_time):
                s_time = self.get_time_from_data_ts(self.k1ms_cache[interval][-1][self.kline_key_open_time]) + timedelta(minutes=1)
            else:
                del self.k1ms_cache[interval]

        k1ms = self.__get_klines_1min(symbol, s_time, e_time)

        if interval in self.k1ms_cache:
            self.k1ms_cache[interval] += k1ms
        else:
            if len(k1ms) == 0:
                return []
            self.k1ms_cache[interval] = k1ms
        return self.k1ms_cache[interval]

    def __get_klines_1min_cache1(self, symbol, interval, s_time, e_time):
        """ 获取分钟k线 """
        if interval not in self.k1ms_cache or (
            interval in self.k1ms_cache
            and self.k1ms_cache_s_time[interval] != s_time
        ):
            # 把整个间隔的分钟k线都取下来
            next_interval_time = s_time + kl.get_interval_timedelta(interval)
            self.k1ms_cache[interval] = self.__get_klines_1min(symbol, s_time, next_interval_time)
            self.k1ms_cache_s_time[interval] = s_time

        tmp_len = int((e_time - s_time).total_seconds() / 60)
        if tmp_len >= len(self.k1ms_cache[interval]):
            return self.k1ms_cache[interval]

        e_timestamp = self.get_data_ts_from_time(e_time)
        while tmp_len > 0:
            if self.k1ms_cache[interval][tmp_len][self.kline_key_open_time] <= e_timestamp:
                break
            tmp_len -= 1
        return self.k1ms_cache[interval][:tmp_len]

    '''
    def __get_info_Klines(self, klines):
        high = float(klines[0]["high"])
        low = float(klines[0]["low"])
        volume = float(klines[0]["volume"])
        for kline in klines[1:]:
            if high < float(kline["high"]):
                high = float(kline["high"])
            if low > float(kline["low"]):
                low = float(kline["low"])
            volume += float(kline["volume"])
        return high, low, volume
    '''

    def __create_kline_from_1min(self, symbol, interval, s_time, e_time):
        """ 取出tick当天开盘到tick时间的分钟k线，生成日k线 """
        k1ms = self.__get_klines_1min_cache1(symbol, interval, s_time, e_time)
        if len(k1ms) == 0:
            return []

        last_k1m = k1ms[-1]
        max_high = float(last_k1m[self.kline_key_high])
        min_low = float(last_k1m[self.kline_key_low])
        total_volume = float(last_k1m[self.kline_key_volume])

        index = len(k1ms) - 2
        while index >= 0:
            k1m = k1ms[index]
            if "max_high" in k1m:
                if max_high < float(k1m["max_high"]):
                    max_high = float(k1m["max_high"])
                if min_low > float(k1m["min_low"]):
                    min_low = float(k1m["min_low"])
                total_volume += float(k1m["total_volume"])
                break
            else:
                if max_high < float(k1m[self.kline_key_high]):
                    max_high = float(k1m[self.kline_key_high])
                if min_low > float(k1m[self.kline_key_low]):
                    min_low = float(k1m[self.kline_key_low])
                total_volume += float(k1m[self.kline_key_volume])
            index -= 1

        last_k1m["max_high"] = max_high
        last_k1m["min_low"] = min_low
        last_k1m["total_volume"] = total_volume

        kline = {
            self.kline_key_open_time: k1ms[0][self.kline_key_open_time],
            self.kline_key_open: k1ms[0][self.kline_key_open],
            self.kline_key_high: max_high,
            self.kline_key_low: min_low,
            self.kline_key_close: k1ms[-1][self.kline_key_close],
            self.kline_key_volume: total_volume,
            self.kline_key_close_time: k1ms[-1][self.kline_key_close_time],
        }
        return [kline]

    '''
    def get_klines_1day(self, symbol, size, since=None):
        """ 获取日k线 """

        # print("tick_time     : ", self.tick_time)
        tick_open_time = get_open_time(self.tick_time)
        # print("tick_open_time: ", tick_open_time)

        if since is None:
            # 取出今天之前的日k线
            e_time = tick_open_time
            s_time = e_time - timedelta(days=size - 1)
        else:
            s_time = get_open_time(since)
            e_time = s_time + timedelta(days=size - 1)

        k1ds = self.__get_klines_1day_cache2(symbol, s_time, e_time)

        k1d = self.__create_klines_1day_from_1min(
            symbol, tick_open_time, self.tick_time
        )

        klines = k1ds + k1d
        return [[(kline[column_name] if (column_name in kline) else "0") for column_name in self.get_kline_column_names()] for kline in klines]

    def __get_klines_1day_cache(self, symbol, s_time, e_time):
        """ 获取分钟k线 """
        if not self.k1ds_cache:
            self.k1ds_cache = self.__get_klines_1day(symbol, s_time, e_time)
            return self.k1ds_cache

        s_index = 0
        s_ts = s_time.timestamp() * 1000
        if s_ts > self.k1ds_cache[0]["open_time"]:
            """缓存数据需要截掉头部多余的"""
            for k1d in self.k1ds_cache:
                if s_ts > k1d["open_time"]:
                    s_index += 1
                elif s_ts == k1d["open_time"]:
                    break
                else:
                    print("1day kline err %s" % k1d)
                    break

        cache_end_time = datetime.fromtimestamp(self.k1ds_cache[-1]["open_time"] / 1000)
        if e_time == cache_end_time:
            return self.k1ds_cache[s_index:]
        elif e_time > cache_end_time:
            self.k1ds_cache += self.__get_klines_1day(
                symbol, cache_end_time + timedelta(days=1), e_time
            )
            return self.k1ds_cache[s_index:]
        else:
            print("err")

    def __get_klines_1day_cache1(self, symbol, s_time, e_time):
        """ 获取分钟k线 """
        if (
            not self.k1ds_cache
            or s_time.timestamp() * 1000 > self.k1ds_cache[0]["open_time"]
            or (e_time - timedelta(days=1)).timestamp() * 1000
            != self.k1ds_cache[-1]["open_time"]
        ):
            self.k1ds_cache = self.__get_klines_1day(symbol, s_time, e_time)

        return self.k1ds_cache

    def __get_klines_1day_cache2(self, symbol, s_time, e_time):
        """ 获取分钟k线 """
        if (
            not self.k1ds_cache
            or s_time != self.k1ds_cache_s_time
            or e_time != self.k1ds_cache_e_time
        ):
            self.k1ds_cache = self.__get_klines_1day(symbol, s_time, e_time)
            self.k1ds_cache_s_time = s_time
            self.k1ds_cache_e_time = e_time

        return self.k1ds_cache
    '''


