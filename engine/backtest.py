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

    def __init__(self, strategy_id, config, *symbols):
        super().__init__(strategy_id, config, DB_ORDERS_NAME)

        self.tick_time = None

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
        k1ms = self._db.find(
            DB_KLINES_1MIN + symbol,
            {
                "open_time": {
                    "$gte": s_time.timestamp() * 1000,
                    "$lt": e_time.timestamp() * 1000,
                }
            },
        )
        # print(k1ms[-1])
        # print("k1ms len: ", len(k1ms))
        # print("k1ms[-1][open_time]: ", datetime.fromtimestamp(k1ms[-1]["open_time"]/1000))
        # print("k1ms[-1][close_time]: ", datetime.fromtimestamp(k1ms[-1]["close_time"]/1000))
        return pd.DataFrame(k1ms)

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

        # 取出tick当天开盘到tick时间的分支k线，生成今天日k线
        # print("tick_time  hour   : ", self.tick_time.hour)
        tick_open_seconds = (self.tick_time - tick_open_time).seconds
        # print("tick_open_seconds     : ", tick_open_seconds)
        k1ms_size = tick_open_seconds // 60
        # print("k1ms_size: ", k1ms_size)
        k1ms = self.get_klines_1min(symbol, k1ms_size, tick_open_time)
        # print("k1ms len ", len(k1ms))
        if len(k1ms) > 0:
            k1ms["volume"] = k1ms["volume"].apply(pd.to_numeric)
            # print('k1ms["volume"] dtype:', k1ms["volume"].dtype)
            k1ds.append(
                {
                    "_id": "",
                    "open_time": k1ms["open_time"].values[0],
                    "open": k1ms["open"].values[0],
                    "close_time": k1ms["close_time"].values[-1],
                    "close": k1ms["close"].values[-1],
                    "high": k1ms["high"].max(),
                    "low": k1ms["low"].min(),
                    "volume": k1ms["volume"].sum(),
                    #"quote_asset_volume": 0,
                    #"number_of_trades": 0,
                    #"taker_buy_base_asset_volume": 0,
                    #"taker_buy_quote_asset_volume": 0,
                    #"ignore": "0",
                }
            )

        k1ds_df = pd.DataFrame(k1ds)
        #del k1ds_df["quote_asset_volume"]
        #del k1ds_df["taker_buy_base_asset_volume"]
        #del k1ds_df["taker_buy_quote_asset_volume"]
        #del k1ds_df["number_of_trades"]
        #del k1ds_df["ignore"]
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

    def send_order_limit(self, side, symbol, cur_price, rate, base_digits, amount):
        """ 提交委托，回测默认以当前价全部成交 """
        limit_price = ts.reserve_float(cur_price * rate, base_digits)
        order_id = uuid.uuid1()
        _id = self._db.insert_one(
            DB_ORDERS_NAME,
            {
                "create_time": self.now().timestamp(),
                "strategy_id": self.strategy_id,
                "symbol": symbol,
                "side": side,
                "type": xq.ORDER_TYPE_LIMIT,
                "pirce": limit_price,
                "amount": amount,
                "status": xq.ORDER_STATUS_CLOSE,
                "order_id": order_id,
                "cancle_amount": 0,
                "deal_amount": amount,
                "deal_value": amount * cur_price,
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
