#!/usr/bin/python
"""实盘"""

import logging
from setup import mongo_user, mongo_pwd, db_name, db_url
from exchange.binanceExchange import BinanceExchange
from exchange.okexExchange import OkexExchange
import common.xquant as xq
import db.mongodb as md
from .engine import Engine


class RealEngine(Engine):
    """实盘引擎"""

    def __init__(self, exchange, strategy_id):
        super().__init__()
        self.strategy_id = strategy_id

        if exchange == "binance":
            self.__exchange = BinanceExchange(debug=True)

        elif exchange == "okex":
            self.__exchange = OkexExchange(debug=True)

        else:
            print("Wrong exchange name: %s" % exchange)
            exit(1)

        self.__db = md.MongoDB(mongo_user, mongo_pwd, db_name, db_url)

    def get_klines_1day(self, symbol, size):
        """ 获取日k线 """
        return self.__exchange.get_klines_1day(symbol, size)

    def get_balances(self, *coins):
        """ 获取余额 """
        return self.__exchange.get_balances(*coins)

    def get_position(self, symbol, cur_price):
        """ 获取持仓信息 """
        self.sync_orders(symbol)

        info = {
            "amount": 0,
            "price": 0,
            "cost": 0,
            "profit": 0,
            "history_profit": 0,
            "start_time": None,
        }
        commission_rate = 0.001

        orders = self.__db.get_orders(strategy_id=self.strategy_id, symbol=symbol)
        for order in orders:
            deal_amount = order["deal_amount"]
            deal_value = order["deal_value"]

            if order["side"] == xq.SIDE_BUY:
                if info["amount"] == 0:
                    info["start_time"] = md.get_datetime_by_id(order["_id"])

                info["amount"] += deal_amount
                info["cost"] += deal_value * (1 + commission_rate)
            elif order["side"] == xq.SIDE_SELL:
                info["amount"] -= deal_amount
                info["cost"] -= deal_value * (1 + commission_rate)
            else:
                logging.error("错误的委托方向")
                continue

            if info["amount"] == 0:
                info["history_profit"] -= info["cost"]
                info["cost"] = 0
                info["start_time"] = None

        if info["amount"] == 0:
            pass
        elif info["amount"] > 0:
            info["profit"] = cur_price * info["amount"] - info["cost"]
            info["price"] = info["cost"] / info["amount"]
        else:
            logging.error("持仓数量不可能小于0")

        logging.info(
            "symbol(%s); current price(%f); position info(%r)", symbol, cur_price, info
        )
        return info

    def has_open_orders(self, symbol):
        """ 是否有open状态的委托 """
        db_orders = self.__db.get_orders(
            strategy_id=self.strategy_id, symbol=symbol, status=xq.ORDER_STATUS_OPEN
        )
        if db_orders:
            return True
        return False

    def sync_orders(self, symbol):
        """ 同步委托。注意：触发是本策略有未完成的委托，但同步是account下所有委托，避免重复查询成交 """
        if not self.has_open_orders(symbol):
            return

        orders = self.__db.get_orders(symbol=symbol, status=xq.ORDER_STATUS_OPEN)
        if not orders:
            return

        df_amount, df_value = self.__exchange.get_deals(symbol)
        for order in orders:
            logging.debug("order: %r", order)
            order_id = order["order_id"]
            order_amount = order["amount"]

            deal_amount = df_amount[order_id]
            deal_value = df_value[order_id]

            status = xq.ORDER_STATUS_OPEN
            if deal_amount > order_amount:
                logging.error("最新成交数量大于委托数量")
                continue
            elif deal_amount == order_amount:
                status = xq.ORDER_STATUS_CLOSE
            else:
                if deal_amount < order["deal_amount"]:
                    logging.warning("最新成交数量小于委托里记载的旧成交数量")
                    continue
                elif deal_amount == order["deal_amount"]:
                    logging.info("成交数量没有更新")
                else:
                    pass
                if self.__exchange.order_status_is_close(symbol, order_id):
                    status = xq.ORDER_STATUS_CLOSE
            logging.debug("deal_amount: %s,  deal_value: %s", deal_amount, deal_value)
            self.__db.update_order(
                _id=order["_id"],
                deal_amount=deal_amount,
                deal_value=deal_value,
                status=status,
            )
        return

    def send_order(self, side, typ, symbol, price, amount):
        """ 提交委托 """
        _id = self.__db.insert_order(
            strategy_id=self.strategy_id,
            symbol=symbol,
            side=side,
            type=typ,
            pirce=price,
            amount=amount,
            status=xq.ORDER_STATUS_WAIT,
            order_id="",
            cancle_amount=0,
            deal_amount=0,
            deal_value=0,
        )

        order_id = self.__exchange.send_order(side, typ, symbol, price, amount, _id)

        self.__db.update_order(_id=_id, order_id=order_id, status=xq.ORDER_STATUS_OPEN)
        return order_id

    def cancle_orders(self, symbol):
        """ 撤掉本策略的所有挂单委托 """
        if not self.has_open_orders(symbol):
            return

        orders = self.__exchange.get_open_orders(symbol)
        for order in orders:
            if order["strategy_id"] == self.strategy_id:
                self.__db.update_order(
                    _id=order["_id"], status=xq.ORDER_STATUS_CANCELLING
                )
                self.__exchange.cancel_order(symbol, order["order_id"])
