#!/usr/bin/python
"""回测环境"""
import sys
from datetime import datetime, timedelta, time
import uuid
import logging
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
        self.k1ms_cache_s_time = None

        self.k1ds_cache = None
        self.k1ds_cache_s_time = None
        self.k1ds_cache_e_time = None

        self.orders = []

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
        return k1ms

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
            {"_id":0},
        )
        return k1ms

    def __get_klines_1min_cache(self, symbol, s_time, e_time):
        """ 获取分钟k线 """
        if self.k1ms_cache:
            if self.k1ms_cache[0]["open_time"] == s_time.timestamp() * 1000:
                s_time = datetime.fromtimestamp(
                    self.k1ms_cache[-1]["open_time"] / 1000
                ) + timedelta(minutes=1)
            else:
                self.k1ms_cache = None

        k1ms = self.__get_klines_1min(symbol, s_time, e_time)

        if self.k1ms_cache:
            self.k1ms_cache += k1ms
        else:
            self.k1ms_cache = k1ms
        return self.k1ms_cache

    def __get_klines_1min_cache1(self, symbol, s_time, e_time):
        """ 获取分钟k线 """
        if not self.k1ms_cache or (
            self.k1ms_cache
            and self.k1ms_cache_s_time != s_time
        ):
            # 把整天的分钟k线都取下来
            next_day_time = s_time + timedelta(days=1)
            self.k1ms_cache = self.__get_klines_1min(symbol, s_time, next_day_time)
            self.k1ms_cache_s_time = s_time

        tmp_len = int((e_time - s_time).total_seconds() / 60)
        if tmp_len >= len(self.k1ms_cache):
            return self.k1ms_cache

        e_timestamp = e_time.timestamp() * 1000
        while tmp_len > 0:
            if self.k1ms_cache[tmp_len]["open_time"] <= e_timestamp:
                break
            tmp_len -= 1
        return self.k1ms_cache[:tmp_len]

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

    def __create_klines_1day_from_1min(self, symbol, s_time, e_time):
        """ 取出tick当天开盘到tick时间的分钟k线，生成日k线 """
        k1ms = self.__get_klines_1min_cache1(symbol, s_time, e_time)
        if len(k1ms) == 0:
            return []

        last_k1m = k1ms[-1]
        max_high = float(last_k1m["high"])
        min_low = float(last_k1m["low"])
        total_volume = float(last_k1m["volume"])

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
                if max_high < float(k1m["high"]):
                    max_high = float(k1m["high"])
                if min_low > float(k1m["low"]):
                    min_low = float(k1m["low"])
                total_volume += float(k1m["volume"])
            index -= 1

        last_k1m["max_high"] = max_high
        last_k1m["min_low"] = min_low
        last_k1m["total_volume"] = total_volume

        k1d = {
            "open_time": k1ms[0]["open_time"],
            "open": k1ms[0]["open"],
            "high": max_high,
            "low": min_low,
            "close": k1ms[-1]["close"],
            "volume": total_volume,
            "close_time": k1ms[-1]["close_time"],
        }
        return [k1d]

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


    def __get_klines_1day(self, symbol, s_time, e_time):
        """ 获取分钟k线 """
        return self._db.find(
            DB_KLINES_1DAY + symbol,
            {
                "open_time": {
                    "$gte": s_time.timestamp() * 1000,
                    "$lt": e_time.timestamp() * 1000,
                }
            },
            {"_id":0},
        )

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
        return self._get_position(symbol, self.orders, cur_price)

    def send_order_limit(
        self, side, symbol, pst_rate, cur_price, limit_price, amount, rmk
    ):
        """ 提交委托，回测默认以当前价全部成交 """
        # order_id = uuid.uuid1()
        order_id = ""
        self.orders.append({
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
        })

        return order_id

    def cancle_orders(self, symbol):
        """ 撤掉本策略的所有挂单委托 """
        pass

    def run(self, strategy, debug):
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

            if debug:
                strategy.on_tick()
            else:
                try:
                    strategy.on_tick()
                except Exception as ept:
                    logging.critical(ept)

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

        symbol = strategy.config["symbol"]
        self.analyze(symbol, self.orders)
        k1ds = self.get_klines_1day(symbol, 100)
        self.display(strategy.config["symbol"], self.orders, k1ds)
