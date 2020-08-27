#!/usr/bin/python
"""回测环境"""
import sys
from datetime import datetime, timedelta, time
import uuid
import utils.tools as ts
import common.xquant as xq
import common.kline as kl
import common.bill as bl
from .engine import Engine
from md.dbmd import DBMD


class BackTest(Engine):
    """回测引擎"""

    def __init__(self, instance_id, exchange_name, config, log_switch=False, *symbols):
        super().__init__(instance_id, config, 10000, log_switch)

        self.md = DBMD(exchange_name, kl.KLINE_DATA_TYPE_JSON)
        self.orders = []

    def now(self):
        return self.md.tick_time

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
        if len(self.orders) > 0:
            if self.orders[-1]["action"] == bl.OPEN_POSITION:
                if "high" not in self.orders[-1] or self.orders[-1]["high"] < cur_price:
                    self.orders[-1]["high"] = cur_price
                    self.orders[-1]["high_time"] = self.now().timestamp()
                if "low" not in self.orders[-1] or self.orders[-1]["low"] > cur_price:
                    self.orders[-1]["low"] = cur_price
                    self.orders[-1]["low_time"] = self.now().timestamp()
        return self._get_position(symbol, self.orders, cur_price)

    def send_order_limit(
        self, direction, action, symbol, pst_rate, cur_price, limit_price, amount, stop_loss_price, rmk
    ):
        """ 提交委托，回测默认以当前价全部成交 """
        # order_id = uuid.uuid1()
        order_id = ""
        self.orders.append({
            "create_time": self.now().timestamp(),
            "instance_id": self.instance_id,
            "symbol": symbol,
            "direction": direction,
            "action": action,
            "pst_rate": pst_rate,
            "type": xq.ORDER_TYPE_LIMIT,
            "market_price": cur_price,
            "price": limit_price,
            "amount": amount,
            "stop_loss_price": stop_loss_price,
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

    def run(self, strategy, start_time, end_time):
        """ run """
        secs = strategy.config["sec"]
        if secs < 60:
            secs = 60
        td_secs = timedelta(seconds=secs)

        pre_tick_cost_time = total_tick_cost_start = datetime.now()
        self.md.tick_time = start_time
        tick_count = 0
        while self.md.tick_time < end_time:
            self.log_info("tick_time: %s" % self.md.tick_time.strftime("%Y-%m-%d %H:%M:%S"))

            strategy.on_tick()

            tick_cost_time = datetime.now()
            self.log_info("tick  cost: %s \n\n" % (tick_cost_time - pre_tick_cost_time))

            tick_count += 1
            self.md.tick_time += td_secs
            progress = (self.md.tick_time - start_time).total_seconds() / (
                end_time - start_time
            ).total_seconds()
            sys.stdout.write(
                "%s  progress: %d%%,  cost: %s,  tick: %s\r"
                % (
                    " "*36,
                    progress * 100,
                    tick_cost_time - total_tick_cost_start,
                    self.md.tick_time.strftime("%Y-%m-%d %H:%M:%S"),
                )
            )
            sys.stdout.flush()

        return tick_count


    def run2(self, strategy, start_time, end_time):
        """ run advance"""
        secs = strategy.config["sec"]
        if secs < 60:
            secs = 60
        td_secs = timedelta(seconds=secs)

        md = self.md
        symbol = strategy.config["symbol"]

        tick_interval = kl.KLINE_INTERVAL_1MINUTE
        tick_collection = kl.get_kline_collection(symbol, tick_interval)
        tick_td = kl.get_interval_timedelta(tick_interval)

        interval = strategy.config["kline"]["interval"]
        interval_collection = kl.get_kline_collection(symbol, interval)
        interval_td = kl.get_interval_timedelta(interval)
        size = strategy.config["kline"]["size"]
        interval_klines = md.get_original_klines(interval_collection, start_time - interval_td * size, end_time)

        if md.kline_data_type == kl.KLINE_DATA_TYPE_JSON and hasattr(strategy, 'json_bt_init'):
            strategy.json_bt_init(interval_klines)

        kl_key_open_time = md.kline_key_open_time
        for i in range(size+1):
            if datetime.fromtimestamp(interval_klines[i][kl_key_open_time]/1000) >= start_time:
                break
        interval_idx = i

        pre_tick_cost_time = total_tick_cost_start = datetime.now()
        tick_count = 0
        for i in range(interval_idx, len(interval_klines)):
            interval_open_time = datetime.fromtimestamp(interval_klines[i][kl_key_open_time]/1000)

            start_i = i - size
            if start_i < 0:
                start_i = 0
            history_kls = interval_klines[start_i:i]
            #print(len(history_kls))

            interval_open_ts = interval_klines[i][kl_key_open_time]
            interval_open_time = datetime.fromtimestamp(interval_open_ts/1000)
            #print(interval_open_time)

            tick_klines = md.get_original_klines(tick_collection, interval_open_time, interval_open_time + interval_td)
            for j, tick_kl in enumerate(tick_klines):
                tick_open_time = datetime.fromtimestamp(tick_kl[kl_key_open_time]/1000)
                self.log_info("tick_time: %s" % tick_open_time.strftime("%Y-%m-%d %H:%M:%S"))
                #print(tick_open_time)
                if j == 0:
                    new_interval_kl = tick_kl
                else:
                    new_interval_kl[md.kline_key_close] = tick_kl[md.kline_key_close]
                    new_interval_kl[md.kline_key_close_time] = tick_kl[md.kline_key_close_time]
                    if new_interval_kl[md.kline_key_high] < tick_kl[md.kline_key_high]:
                        new_interval_kl[md.kline_key_high] = tick_kl[md.kline_key_high]
                    if new_interval_kl[md.kline_key_low] > tick_kl[md.kline_key_low]:
                        new_interval_kl[md.kline_key_low] = tick_kl[md.kline_key_low]

                kls = history_kls + [new_interval_kl]
                if md.kline_data_type == kl.KLINE_DATA_TYPE_LIST:
                    kls = kl.trans_from_json_to_list(kls, md.kline_column_names)
                md.tick_time = tick_open_time + tick_td
                strategy.on_tick(kls)

                tick_cost_time = datetime.now()
                self.log_info("tick  cost: %s \n\n" % (tick_cost_time - pre_tick_cost_time))
                pre_tick_cost_time = tick_cost_time
                tick_count += 1

            progress = (i + 1 - interval_idx) / (len(interval_klines) - interval_idx)
            sys.stdout.write(
                "%s  progress: %d%%,  cost: %s, next open time: %s\r"
                % (
                    " "*36,
                    progress * 100,
                    tick_cost_time - total_tick_cost_start,
                    (interval_open_time+interval_td).strftime("%Y-%m-%d %H:%M:%S"),
                )
            )
            sys.stdout.flush()

        return tick_count


    def refresh(self, strategy, times):
        """ refresh """
        total_tick_count = len(times)
        total_tick_start = datetime.now()
        tick_count = 0
        for t in times:
            self.md.tick_time = t
            self.log_info("tick_time: %s" % self.md.tick_time.strftime("%Y-%m-%d %H:%M:%S"))
            tick_start = datetime.now()

            strategy.on_tick()

            tick_end = datetime.now()
            self.log_info("tick  cost: %s \n\n" % (tick_end - tick_start))

            tick_count += 1
            progress = tick_count / total_tick_count
            sys.stdout.write(
                "%s  progress: %d%%,  cost: %s,  tick: %s\r"
                % (
                    " "*36,
                    progress * 100,
                    tick_end - total_tick_start,
                    self.md.tick_time.strftime("%Y-%m-%d %H:%M:%S"),
                )
            )
            sys.stdout.flush()

        total_tick_end = datetime.now()
        print(
            "\n  total tick count: %d cost: %s"
            % (tick_count, total_tick_end - total_tick_start)
        )

