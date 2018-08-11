#!/usr/bin/python
"""运行环境引擎"""
from datetime import datetime
import logging
from setup import mongo_user, mongo_pwd, db_name, db_url
import common.xquant as xq
import db.mongodb as md


class Engine:
    """引擎"""

    def __init__(self, strategy_id, db_orders_name):
        self.strategy_id = strategy_id
        self.db_orders_name = db_orders_name
        self._db = md.MongoDB(mongo_user, mongo_pwd, db_name, db_url)

    def _get_position(self, symbol, cur_price, limit_base_amount):
        info = {
            "amount": 0,
            "price": 0,
            "cost": 0,
            "profit": 0,
            "history_profit": 0,
            "start_time": None,
        }
        commission_rate = 0.001

        orders = self._db.find(
            self.db_orders_name, {"strategy_id": self.strategy_id, "symbol": symbol}
        )
        for order in orders:
            deal_amount = order["deal_amount"]
            deal_value = order["deal_value"]

            if order["side"] == xq.SIDE_BUY:
                if info["amount"] == 0:
                    info["start_time"] = datetime.fromtimestamp(order["create_time"])

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

        info["limit_base_amount"] = limit_base_amount
        info["total_profit_rate"] = (
            info["profit"] + info["history_profit"]
        ) / limit_base_amount

        logging.info(
            "symbol( %s ); current price( %g ); position(amount: %g,  price: %g,  cost: %g,  profit: %g,  history_profit: %g,  limit: %g,  total_profit_rate: %g%s )",
            symbol,
            cur_price,
            info["amount"],
            info["price"],
            info["cost"],
            info["profit"],
            info["history_profit"],
            info["limit_base_amount"],
            info["total_profit_rate"],
            ",  start_time: %s" % info["start_time"].strftime("%Y-%m-%d %H:%M:%S")
            if info["start_time"]
            else "",
        )
        # print(info)
        return info
