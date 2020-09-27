#!/usr/bin/python
"""实盘"""
import time
import datetime
import utils.tools as ts
import common.xquant as xq
import common.kline as kl
import common.bill as bl
from .engine import Engine
from .order import get_floating_profit, POSITON_COMMISSION_KEY
from exchange.exchange import create_exchange
from md.exmd import ExchangeMD
from db.mongodb import get_mongodb
import setup


DB_ORDERS_NAME = "orders"


class RealEngine(Engine):
    """实盘引擎"""

    def __init__(self, instance_id, exchange_name, config, value, log_switch=False):
        super().__init__(instance_id, config, value, log_switch)

        self.db_orders_name = DB_ORDERS_NAME
        self.td_db = get_mongodb(setup.trade_db_name)
        self.td_db.ensure_index(self.db_orders_name, [("instance_id",1),("symbol",1)])

        self.__exchange = create_exchange(exchange_name)
        if not self.__exchange:
            print("Wrong exchange name: %s" % exchange_name)
            exit(1)

        self.md = ExchangeMD(self.__exchange, kl.KLINE_DATA_TYPE_JSON)

    def now(self):
        return datetime.datetime.now()

    def get_account(self):
        """ 获取账户信息 """
        return self.__exchange.get_account()

    def get_balances(self, *coins):
        """ 获取余额 """
        return self.__exchange.get_balances(*coins)

    def get_position(self, symbol, cur_price):
        """ 获取持仓信息 """
        self.sync_orders(symbol)

        orders = self.get_orders(symbol)

        if len(orders) > 0:
            now_ts = self.now().timestamp()

            if orders[-1]["action"] == bl.OPEN_POSITION:
                if "high" not in orders[-1] or orders[-1]["high"] < cur_price:
                    orders[-1]["high"] = cur_price
                    orders[-1]["high_time"] = now_ts
                    self.td_db.update_one(
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
                    self.td_db.update_one(
                        self.db_orders_name,
                        orders[-1]["_id"],
                        {
                            "low": cur_price,
                            "low_time": now_ts,
                        },
                    )

        return self._get_position(symbol, orders, cur_price)


    def get_orders(self, symbol):
        return self.td_db.find(
            DB_ORDERS_NAME,
            {
                "instance_id": self.instance_id,
                "symbol": symbol,
            },
        )


    def get_open_orders(self, symbol):
        """ 是否有open状态的委托 """
        return self.td_db.find(
            DB_ORDERS_NAME,
            {
                "instance_id": self.instance_id,
                "symbol": symbol,
                "status": xq.ORDER_STATUS_OPEN,
            },
        )

    def sync_orders(self, symbol):
        orders = self.get_open_orders(symbol)
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
            self.td_db.update_one(
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
        self, direction, action, symbol, pst_rate, cur_price, limit_price, amount, stop_loss_price, rmk
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
            direction, action, xq.ORDER_TYPE_LIMIT, symbol, limit_price, amount
        )

        _id = self.td_db.insert_one(
            DB_ORDERS_NAME,
            {
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
        orders = self.get_open_orders(symbol)
        if not orders:
            return

        e_order_ids = self.__exchange.get_open_order_ids(symbol)

        for order in orders:
            order_id = order["order_id"]
            if order_id not in e_order_ids:
                continue
            self.__exchange.cancel_order(symbol, order_id)
            self.td_db.update_one(
                DB_ORDERS_NAME, order["_id"], {"status": xq.ORDER_STATUS_CANCELLING}
            )


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

    def view(self, symbol, orders):
        if len(orders) == 0:
            return

        self.view_history(symbol, orders)

        kls = self.md.get_klines_1day(symbol, 1)
        cur_price = float(kls[-1][self.md.get_kline_seat_close()])
        floating_profit = get_floating_profit(pst_info, cur_price)
        open_value = self.value
        if self.config["mode"] == 1:
            open_value += history_profit
        floating_profit_rate = floating_profit / open_value
        floating_commission  = pst_info[POSITON_COMMISSION_KEY]
        print("floating:  profit = %.2f(%.2f%%)    commission = %.2f" % (floating_profit, floating_profit_rate*100, floating_commission))

