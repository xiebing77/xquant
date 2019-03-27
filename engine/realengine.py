#!/usr/bin/python
"""实盘"""
import time
import datetime
import utils.tools as ts
import common.xquant as xq
from .engine import Engine
from exchange.binanceExchange import BinanceExchange
from exchange.okexExchange import OkexExchange


DB_ORDERS_NAME = "orders"


class RealEngine(Engine):
    """实盘引擎"""

    def __init__(self, instance_id, config):
        super().__init__(instance_id, config, DB_ORDERS_NAME)

        exchange = config["exchange"]
        if exchange == "binance":
            self.__exchange = BinanceExchange(debug=True)

        elif exchange == "okex":
            self.__exchange = OkexExchange(debug=True)

        else:
            print("Wrong exchange name: %s" % exchange)
            exit(1)

    def now(self):
        return datetime.datetime.now()

    def get_klines(self, symbol, interval, size):
        """ 获取日k线 """
        return self.__exchange.get_klines(symbol, interval, size)

    def get_klines_1day(self, symbol, size):
        """ 获取日k线 """
        return self.__exchange.get_klines_1day(symbol, size)

    def get_balances(self, *coins):
        """ 获取余额 """
        return self.__exchange.get_balances(*coins)

    def get_position(self, symbol, cur_price):
        """ 获取持仓信息 """
        self.sync_orders(symbol)

        orders = self._db.find(self.db_orders_name, {"instance_id": self.instance_id, "symbol": symbol})

        if len(orders) > 0:
            now_ts = self.now().timestamp()

            if orders[-1]["side"] == xq.SIDE_BUY:
                if "high" not in orders[-1] or orders[-1]["high"] < cur_price:
                    orders[-1]["high"] = cur_price
                    orders[-1]["high_time"] = now_ts
                    self._db.update_one(
                        self.db_orders_name,
                        orders[-1]["_id"],
                        {
                            "high": cur_price,
                            "high_time": now_ts,
                        },
                    )

                if "low" not in orders[-1] or orders[-1]["low"] > cur_price:
                    orders[-1]["low"] = cur_price
                    orders[-1]["low_time"] = now_ts
                    self._db.update_one(
                        self.db_orders_name,
                        orders[-1]["_id"],
                        {
                            "low": cur_price,
                            "low_time": now_ts,
                        },
                    )

        return self._get_position(symbol, orders, cur_price)

    def has_open_orders(self, symbol):
        """ 是否有open状态的委托 """
        db_orders = self._db.find(
            DB_ORDERS_NAME,
            {
                "instance_id": self.instance_id,
                "symbol": symbol,
                "status": xq.ORDER_STATUS_OPEN,
            },
        )
        if db_orders:
            return True
        return False

    def sync_orders(self, symbol):
        """ 同步委托。注意：触发是本策略有未完成的委托，但同步是account下所有委托，避免重复查询成交 """
        if not self.has_open_orders(symbol):
            return
        orders = self._db.find(
            DB_ORDERS_NAME, {"symbol": symbol, "status": xq.ORDER_STATUS_OPEN}
        )
        if not orders:
            return

        df_amount, df_value = self.__exchange.get_deals(symbol)
        for order in orders:
            self.log_debug("order: %r" % order)
            order_id = order["order_id"]
            order_amount = order["amount"]

            if order_id not in df_amount.index:
                """ 没有成交信息 """
                continue

            deal_amount = df_amount[order_id]

            target_coin, base_coin = xq.get_symbol_coins(symbol)
            deal_amount = ts.reserve_float(deal_amount, self.config["digits"][target_coin])
            deal_value = df_value[order_id]

            status = xq.ORDER_STATUS_OPEN
            if deal_amount > order_amount:
                self.log_error("最新成交数量(%f)大于委托数量(%f)  %g" % (deal_amount, order_amount, (deal_amount-order_amount)))
                continue
            elif deal_amount == order_amount:
                status = xq.ORDER_STATUS_CLOSE
            else:
                if deal_amount < order["deal_amount"]:
                    self.log_warning("最新成交数量小于委托里记载的旧成交数量")
                    continue
                elif deal_amount == order["deal_amount"]:
                    self.log_info("成交数量没有更新")
                else:
                    pass
                if self.__exchange.order_status_is_close(symbol, order_id):
                    status = xq.ORDER_STATUS_CLOSE
            self.log_debug("deal_amount: %f,  deal_value: %g,  deal_price: %g" % (deal_amount, deal_value, deal_value/deal_amount))
            self._db.update_one(
                DB_ORDERS_NAME,
                order["_id"],
                {
                    "deal_amount": deal_amount,
                    "deal_value": deal_value,
                    "status": status,
                },
            )
        return

    def send_order_limit(
        self, side, symbol, pst_rate, cur_price, limit_price, amount, rmk
    ):
        """ 提交委托 """
        """
        _id = self._db.insert_one(
            DB_ORDERS_NAME,
            {
                "create_time": self.now().timestamp(),
                "instance_id": self.instance_id,
                "symbol": symbol,
                "side": side,
                "pst_rate": pst_rate,
                "type": xq.ORDER_TYPE_LIMIT,
                "price": limit_price,
                "amount": amount,
                "status": xq.ORDER_STATUS_WAIT,
                "order_id": "",
                "cancle_amount": 0,
                "deal_amount": 0,
                "deal_value": 0,
            },
        )

        order_id = self.__exchange.send_order(
            side, xq.ORDER_TYPE_LIMIT, symbol, limit_price, amount, _id
        )

        self._db.update_one(
            DB_ORDERS_NAME, _id, {"order_id": order_id, "status": xq.ORDER_STATUS_OPEN}
        )
        """
        # 暂时简单处理
        order_id = self.__exchange.send_order(
            side, xq.ORDER_TYPE_LIMIT, symbol, limit_price, amount
        )

        _id = self._db.insert_one(
            DB_ORDERS_NAME,
            {
                "create_time": self.now().timestamp(),
                "instance_id": self.instance_id,
                "symbol": symbol,
                "side": side,
                "pst_rate": pst_rate,
                "type": xq.ORDER_TYPE_LIMIT,
                "market_price": cur_price,
                "price": limit_price,
                "amount": amount,
                "status": xq.ORDER_STATUS_OPEN,
                "order_id": order_id,
                "cancle_amount": 0,
                "deal_amount": 0,
                "deal_value": 0,
                "rmk": rmk,
            },
        )

        return order_id

    def cancle_orders(self, symbol):
        """ 撤掉本策略的所有挂单委托 """
        if not self.has_open_orders(symbol):
            return

        orders = self.__exchange.get_open_orders(symbol)
        for order in orders:
            if order["instance_id"] == self.instance_id:
                self._db.update_one(
                    DB_ORDERS_NAME, order["_id"], {"status": xq.ORDER_STATUS_CANCELLING}
                )
                self.__exchange.cancel_order(symbol, order["order_id"])

    def run(self, strategy, debug):
        """ run """
        while True:
            tick_start = datetime.datetime.now()
            self.log_info(
                "%s tick start......................................" % tick_start
            )

            if debug:
                strategy.on_tick()
            else:
                try:
                    strategy.on_tick()
                except Exception as ept:
                    self.log_critical(ept)

            tick_end = datetime.datetime.now()
            self.log_info(
                "%s tick end...; tick  cost: %s -----------------------\n\n" % (
                tick_end,
                tick_end - tick_start
                )
            )
            time.sleep(strategy.config["sec"])
