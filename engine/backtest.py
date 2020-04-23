#!/usr/bin/python
"""回测环境"""
import sys
from datetime import datetime, timedelta, time
import uuid
import utils.tools as ts
import common.xquant as xq
import common.bill as bl
import db.mongodb as md
from .engine import Engine
from md.dbmd import DBMD


class BackTest(Engine):
    """回测引擎"""

    def __init__(self, instance_id, exchange_name, config, value=10000, *symbols):
        super().__init__(instance_id, config, value)

        self.md = DBMD(exchange_name)
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

    def run(self, strategy, start_time, end_time, args):
        """ run """
        total_tick_start = datetime.now()
        self.md.tick_time = start_time
        tick_count = 0
        while self.md.tick_time < end_time:
            self.log_info("tick_time: %s" % self.md.tick_time.strftime("%Y-%m-%d %H:%M:%S"))
            tick_start = datetime.now()

            strategy.on_tick()

            tick_end = datetime.now()
            self.log_info("tick  cost: %s \n\n" % (tick_end - tick_start))

            tick_count += 1
            self.md.tick_time += timedelta(seconds=strategy.config["sec"])
            progress = (self.md.tick_time - start_time).total_seconds() / (
                end_time - start_time
            ).total_seconds()
            sys.stdout.write(
                "  tick: %s,  cost: %s,  progress: %d%% \r"
                % (
                    self.md.tick_time.strftime("%Y-%m-%d %H:%M:%S"),
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

        if args.cs:
            interval = strategy.config["kline"]["interval"]
            display_count = int((end_time - start_time).total_seconds()/xq.get_interval_seconds(interval))
            print("display_count: %s" % display_count)
            klines = self.md.get_klines(symbol, interval, 150+display_count)
            self.display(args, symbol, self.orders, klines, display_count)
