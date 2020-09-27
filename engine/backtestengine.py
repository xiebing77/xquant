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

    def view(self, symbol, orders):
        if len(orders) == 0:
            return

        self.view_history(symbol, orders)

