#!/usr/bin/python
"""运行环境引擎"""
from datetime import datetime
import logging
from setup import mongo_user, mongo_pwd, db_name, db_url
import common.xquant as xq
import db.mongodb as md


class Engine:
    """引擎"""

    def __init__(self, strategy_id, config, db_orders_name):
        self.strategy_id = strategy_id
        self.config = config
        self.db_orders_name = db_orders_name
        self._db = md.MongoDB(mongo_user, mongo_pwd, db_name, db_url)

    def _get_position(self, symbol, cur_price, limit_base_amount):
        info = {
            "amount": 0,     # 数量
            "price": 0,      # 平均价格，不包含佣金
            "cost_price": 0, # 分摊佣金后的成本价
            "value": 0,      # 剩余金额，用于计算均价
            "commission": 0, # 佣金
            "cost": 0,       # 成本，等于金额+佣金
            "profit": 0,     # 当前利润
            "history_profit": 0, # 历史利润
            "start_time": None,  # 本周期第一笔买入时间
        }
        commission_rate = 0.001

        orders = self._db.find(
            self.db_orders_name, {"strategy_id": self.strategy_id, "symbol": symbol}
        )
        for order in orders:
            deal_amount = order["deal_amount"]
            deal_value = order["deal_value"]
            commission = deal_value * commission_rate

            if order["side"] == xq.SIDE_BUY:
                if info["amount"] == 0:
                    info["start_time"] = datetime.fromtimestamp(order["create_time"])

                info["amount"] += deal_amount

                info["value"] += deal_value

                info["cost"] += deal_value 
                info["cost"] += commission

            elif order["side"] == xq.SIDE_SELL:
                info["amount"] -= deal_amount
                
                info["value"] -= deal_value

                info["cost"] -= deal_value 
                info["cost"] += commission
            else:
                logging.error("错误的委托方向")
                continue

            if info["amount"] == 0:
                info["history_profit"] -= info["cost"]
                info["value"] = 0
                info["cost"] = 0
                info["start_time"] = None

        if info["amount"] == 0:
            pass
        elif info["amount"] > 0:
            info["profit"] = cur_price * info["amount"] - info["cost"]
            info["price"] = info["value"] / info["amount"]
            info["cost_price"] = info["cost"] / info["amount"]

        else:
            logging.error("持仓数量不可能小于0")

        info["limit_base_amount"] = limit_base_amount["value"]

        logging.info(
            "symbol( %s ); current price( %g ); position(%s%s%s  history_profit: %g,  total_profit_rate: %g)",
            symbol,
            cur_price,
            "amount: %g,  price: %g, cost price: %g,  cost: %g,  limit: %g,  profit: %g," % (info["amount"],info["price"],info["cost_price"],info["cost"],info["limit_base_amount"],info["profit"]) if info["amount"] else "",
            "  profit rate: %g," % (info["profit"] / info["cost"]) if info["cost"] else "",
            "  start_time: %s\n," % info["start_time"].strftime("%Y-%m-%d %H:%M:%S") if info["start_time"] else "",
            info["history_profit"],
            (info["profit"] + info["history_profit"]) / info["limit_base_amount"],
        )
        # print(info)
        return info
