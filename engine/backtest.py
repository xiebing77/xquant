#!/usr/bin/python
"""回测环境"""
import sys
from datetime import datetime, timedelta, time
import uuid
import logging
import pandas as pd
import utils.tools as ts
import common.xquant as xq
import db.mongodb as md
from .engine import Engine


DB_KLINES_1MIN = "kline_"
DB_KLINES_1DAY = "kline_1day_"
DB_KLINES_INDEX = "open_time"

DB_ORDERS_NAME = "bt_orders"

MINS_ON_DAY = 60 * 24


def get_open_time(dt):
    if dt.hour < 8:
        open_time = datetime.combine(dt.date() - timedelta(days=1), time(8, 0, 0))
    else:
        open_time = datetime.combine(dt.date(), time(8, 0, 0))
    return open_time


class BackTest(Engine):
    """回测引擎"""

    def __init__(self, instance_id, config, *symbols):
        super().__init__(instance_id, config, DB_ORDERS_NAME)

        self.tick_time = None

        self.k1ms_cache = None

    def now(self):
        return self.tick_time

    def get_klines_1min(self, symbol, size, since=None):
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

        k1ms = self.__get_klines_1min_cache(symbol, s_time, e_time)
        return pd.DataFrame(k1ms)

    def __get_klines_1min(self, symbol, s_time, e_time):
        """ 获取分钟k线 """
        k1ms = self._db.find(
            DB_KLINES_1MIN + symbol,
            {
                "open_time": {
                    "$gte": s_time.timestamp() * 1000,
                    "$lt": e_time.timestamp() * 1000,
                }
            },
        )
        return k1ms

    def __get_klines_1min_cache(self, symbol, s_time, e_time):
        """ 获取分钟k线 """
        if self.k1ms_cache:
            if self.k1ms_cache[0]["open_time"] == s_time.timestamp() * 1000:
                s_time = datetime.fromtimestamp(self.k1ms_cache[-1]["open_time"]/1000) + timedelta(minutes=1)
            else:
                self.k1ms_cache = None

        k1ms = self._db.find(
            DB_KLINES_1MIN + symbol,
            {
                "open_time": {
                    "$gte": s_time.timestamp() * 1000,
                    "$lt": e_time.timestamp() * 1000,
                }
            },
        )

        if self.k1ms_cache:
            self.k1ms_cache += k1ms
        else:
            self.k1ms_cache = k1ms
        return self.k1ms_cache

    def __get_klines_1min_cache2(self, symbol, s_time, e_time):
        """ 获取分钟k线 """
        if not self.k1ms_cache or (self.k1ms_cache and self.k1ms_cache[0]["open_time"] != s_time.timestamp() * 1000):
            self.k1ms_cache_cursor = int((e_time-s_time).total_seconds()/60)
            #print("self.k1ms_cache_cursor:", self.k1ms_cache_cursor)

            next_day_time = s_time + timedelta(days=1)
            self.k1ms_cache = self._db.find(
                DB_KLINES_1MIN + symbol,
                {
                    "open_time": {
                        "$gte": s_time.timestamp() * 1000,
                        "$lt": next_day_time.timestamp() * 1000,
                    }
                },
            )
            # print("next_day_time: ",next_day_time)
            # size = len(self.k1ms_cache)
            # print("k1ms_cache size: ", size)

            """
            open_time = self.k1ms_cache[0]["open_time"]
            if open_time != s_time.timestamp() * 1000:
                print("miss open_time:%s, s_time:%s,%s"%(open_time,s_time,s_time.timestamp() * 1000))

            for k1m in self.k1ms_cache[1:]:
                if k1m["open_time"] <= open_time:
                    print("k1ms_cache: ", self.k1ms_cache)
                    break
                else:
                    open_time = k1m["open_time"]
            """

            """
            td = timedelta(minutes=1)
            i = 0
            tick_time = s_time
            while tick_time < next_day_time:
                ts = int(tick_time.timestamp()*1000)
                #print(ts, " ~ ", klines[i]["open_time"])
                if ts ==self.k1ms_cache[i]["open_time"]:
                    #print(tick_time, " match  ok")
                    pass
                else:
                    k1ms_cache_df = pd.DataFrame(self.k1ms_cache)
                    #k1ms_cache_df["open_time"] = datetime.fromtimestamp(k1ms_cache_df["open_time"]/1000)
                    print(k1ms_cache_df)

                tick_time += td
                i += 1
            """

        size = len(self.k1ms_cache)
        #print("k1ms_cache size: ", size)
        if size == 60*24:
            k1ms = self.k1ms_cache[:int((e_time-s_time).total_seconds()/60)]
            #print("xxx k1ms size: ", len(k1ms))
        else:
            while self.k1ms_cache_cursor < size:
                k1m = self.k1ms_cache[self.k1ms_cache_cursor]
                if k1m["open_time"] >= e_time.timestamp()*1000:
                    break
                self.k1ms_cache_cursor += 1
            k1ms = self.k1ms_cache[:self.k1ms_cache_cursor]

        # print(k1ms[-1])
        # print("k1ms len: ", len(k1ms))
        # print("k1ms[-1][open_time]: ", datetime.fromtimestamp(k1ms[-1]["open_time"]/1000))
        # print("k1ms[-1][close_time]: ", datetime.fromtimestamp(k1ms[-1]["close_time"]/1000))
        return k1ms

    def __create_klines_1day_from_1min(self, symbol, s_time, e_time):
        """ 取出tick当天开盘到tick时间的分钟k线，生成日k线 """
        k1ms = self.__get_klines_1min_cache(symbol, s_time, e_time)
        if len(k1ms) == 0:
            return None

        high = k1ms[0]["high"]
        low = k1ms[0]["low"]
        volume = k1ms[0]["volume"]
        for k1m in k1ms[1:]:
            if high < k1m["high"]:
                high = k1m["high"]
            if low > k1m["low"]:
                low = k1m["low"]
            volume += k1m["volume"]

        k1d = {
            "_id": "",
            "open_time": k1ms[0]["open_time"],
            "open": k1ms[0]["open"],
            "close_time": k1ms[-1]["close_time"],
            "close": k1ms[-1]["close"],
            "high": high,
            "low": low,
            "volume": volume,
        }
        return k1d

    def get_klines_1day(self, symbol, size, since=None):
        """ 获取日k线 """

        # print("tick_time     : ", self.tick_time)
        tick_open_time = get_open_time(self.tick_time)
        # print("tick_open_time: ", tick_open_time)

        # 取出今天之前的日k线
        if since is None:
            e_time = tick_open_time
            s_time = e_time - timedelta(days=size - 1)
        else:
            s_time = get_open_time(since)
            e_time = s_time + timedelta(minutes=size - 1)

        # print("1day s_time:",s_time)
        # print("1day e_time:",e_time)
        # print("1day s_time timestamp: ",s_time.timestamp())
        # print("1day e_time timestamp: ",e_time.timestamp())
        k1ds = self._db.find(
            DB_KLINES_1DAY + symbol,
            {
                "open_time": {
                    "$gte": s_time.timestamp() * 1000,
                    "$lt": e_time.timestamp() * 1000,
                }
            },
        )
        # print("k1ds len: ", len(k1ds))
        # print(k1ds[-1])
        # print("k1ds[-1][open_time]: ", datetime.fromtimestamp(k1ds[-1]["open_time"]/1000))
        # print("k1ds[-1][close_time]: ", datetime.fromtimestamp(k1ds[-1]["close_time"]/1000))

        k1d = self.__create_klines_1day_from_1min(symbol, tick_open_time, self.tick_time)
        if k1d:
            k1ds.append(k1d)

        k1ds_df = pd.DataFrame(k1ds)
        # del k1ds_df["quote_asset_volume"]
        # del k1ds_df["taker_buy_base_asset_volume"]
        # del k1ds_df["taker_buy_quote_asset_volume"]
        # del k1ds_df["number_of_trades"]
        # del k1ds_df["ignore"]
        return k1ds_df


    def get_balances(self, *coins):
        """ 获取账户余额，回测默认1个亿，哈哈 """
        coin_balances = []
        for coin in coins:
            balance = xq.create_balance(coin, "100000000", "0")
            coin_balances.append(balance)

        if len(coin_balances) <= 0:
            return
        elif len(coin_balances) == 1:
            return coin_balances[0]
        else:
            return tuple(coin_balances)

    def get_position(self, symbol, cur_price):
        """ 获取持仓信息 """
        return self._get_position(symbol, cur_price)

    def send_order_limit(
        self, side, symbol, pst_rate, cur_price, limit_price, amount, rmk
    ):
        """ 提交委托，回测默认以当前价全部成交 """
        # order_id = uuid.uuid1()
        order_id = ""
        _id = self._db.insert_one(
            DB_ORDERS_NAME,
            {
                "create_time": self.now().timestamp(),
                "instance_id": self.instance_id,
                "symbol": symbol,
                "side": side,
                "pst_rate": pst_rate,
                "type": xq.ORDER_TYPE_LIMIT,
                "pirce": limit_price,
                "amount": amount,
                "status": xq.ORDER_STATUS_CLOSE,
                "order_id": order_id,
                "cancle_amount": 0,
                "deal_amount": amount,
                "deal_value": amount * cur_price,
                "rmk": rmk,
            },
        )

        return order_id

    def cancle_orders(self, symbol):
        """ 撤掉本策略的所有挂单委托 """
        pass

    def run(self, strategy):
        """ run """
        print(
            "backtest time range: [ %s , %s )"
            % (
                self.config["backtest"]["start_time"],
                self.config["backtest"]["end_time"],
            )
        )

        start_time = datetime.strptime(
            self.config["backtest"]["start_time"], "%Y-%m-%d %H:%M:%S"
        )
        end_time = datetime.strptime(
            self.config["backtest"]["end_time"], "%Y-%m-%d %H:%M:%S"
        )

        total_tick_start = datetime.now()
        self.tick_time = start_time
        tick_count = 0
        while self.tick_time < end_time:
            logging.info("tick_time: %s", self.tick_time.strftime("%Y-%m-%d %H:%M:%S"))
            tick_start = datetime.now()
            strategy.on_tick()
            tick_end = datetime.now()
            logging.info("tick  cost: %s \n\n", tick_end - tick_start)

            tick_count += 1
            self.tick_time += timedelta(seconds=strategy.config["sec"])
            progress = (self.tick_time - start_time).total_seconds() / (
                end_time - start_time
            ).total_seconds()
            sys.stdout.write(
                "  tick: %s,  cost: %s,  progress: %d%% \r"
                % (
                    self.tick_time.strftime("%Y-%m-%d %H:%M:%S"),
                    tick_end - total_tick_start,
                    progress * 100,
                )
            )
            sys.stdout.flush()

        total_tick_end = datetime.now()
        print(
            "\n  total tick count: %d cost: %s"
            % (tick_count, total_tick_end - total_tick_start)
        )

        self.analyze(strategy.config["symbol"])
