#!/usr/bin/python
"""strategy"""

import time
import datetime
import logging
from engine.realengine import RealEngine
import common.xquant as xq
import utils.tools as ts


class Strategy:
    """Strategy"""

    def __init__(self, config, debug):
        self.config = config
        self.debug_flag = debug

        self.instance_id = (
            self.__class__.__name__
            + "_"
            + self.config["symbol"]
            + "_"
            + self.config["id"]
        )

        logfilename = (
            self.instance_id + "_" + datetime.datetime.now().strftime("%Y%m%d") + ".log"
        )
        print(logfilename)
        logging.basicConfig(level=logging.NOTSET, filename=logfilename)

        logging.info("strategy name: %s;  config: %s", self.__class__.__name__, config)

        self.engine = RealEngine(self.config["exchange"], self.instance_id)

    def risk_control(self, position_info):
        """ 风控 """
        rc_side = None
        rc_position_rate = 1

        # 风控第一条：亏损金额超过额度的10%，如额度1000，亏损金额超过100即刻清仓
        loss_limit = self.config["limit"] * 0.1
        if loss_limit + position_info["profit"] <= 0:
            rc_side = xq.SIDE_SELL
            rc_position_rate = min(0, rc_position_rate)

        return rc_side, rc_position_rate

    def handle_order(
        self, symbol, cur_price, desired_side, desired_position_rate, position_info
    ):
        """
        风控与期望的关系
        风控方向只能是None、sell
        None：说明风控没有触发。以期望方向、仓位率为准
        sell：说明风控被触发。若期望为买或空，则以风控为主；若期望也为卖，则仓位率取少的
        """
        rc_side, rc_position_rate = self.risk_control(position_info)
        if rc_side == xq.SIDE_BUY:
            logging.warning("风控方向不能为买")
            return

        if rc_side == xq.SIDE_SELL:
            if desired_side == xq.SIDE_SELL:
                desired_position_rate = min(rc_position_rate, desired_position_rate)
            else:
                desired_side = xq.SIDE_SELL
                desired_position_rate = rc_position_rate

        if desired_position_rate > 1 or desired_position_rate < 0:
            logging.warning("仓位率（%f）超出范围（0 ~ 1）", desired_position_rate)
            return

        if desired_side == xq.SIDE_BUY:
            buy_base_amount = (
                self.config["limit"] * desired_position_rate - position_info["cost"]
            )
            self.limit_buy(symbol, ts.reserve_float(buy_base_amount), cur_price)
        elif desired_side == xq.SIDE_SELL:
            if position_info["cost"] == 0:
                return
            position_rate = position_info["cost"] / self.config["limit"]
            desired_position_amount = (
                position_info["amount"] * desired_position_rate / position_rate
            )

            target_coin, _ = xq.get_symbol_coins(symbol)
            sell_target_amount = position_info["amount"] - ts.reserve_float(
                desired_position_amount, self.config["digits"][target_coin]
            )
            self.limit_sell(symbol, sell_target_amount, cur_price)
        else:
            return

    def limit_buy(self, symbol, base_coin_amount, cur_price):
        """ 限价买 """
        if base_coin_amount <= 0:
            return

        target_coin, base_coin = xq.get_symbol_coins(symbol)
        base_balance = self.engine.get_balances(base_coin)
        logging.info("base   balance:  %s", base_balance)

        buy_base_amount = min(xq.get_balance_free(base_balance), base_coin_amount)
        logging.info("buy_base_amount: %f", buy_base_amount)

        if buy_base_amount <= 0:  #
            return

        target_amount_digits = self.config["digits"][target_coin]
        buy_target_amount = ts.reserve_float(
            buy_base_amount / cur_price, target_amount_digits
        )
        logging.info("buy target coin amount: %f", buy_target_amount)

        base_amount_digits = self.config["digits"][base_coin]
        limit_buy_price = ts.reserve_float(cur_price * 1.1, base_amount_digits)
        order_id = self.engine.send_order(
            xq.SIDE_BUY, xq.ORDER_TYPE_LIMIT, symbol, limit_buy_price, buy_target_amount
        )
        logging.info(
            "current price: %f;  limit buy price: %f;  order_id: %s ",
            cur_price,
            limit_buy_price,
            order_id,
        )
        return

    def limit_sell(self, symbol, target_coin_amount, cur_price):
        """ 限价卖 """
        if target_coin_amount <= 0:
            return
        logging.info("sell target coin num: %f", target_coin_amount)

        _, base_coin = xq.get_symbol_coins(symbol)
        base_amount_digits = self.config["digits"][base_coin]
        limit_sell_price = ts.reserve_float(cur_price * 0.9, base_amount_digits)
        order_id = self.engine.send_order(
            xq.SIDE_SELL,
            xq.ORDER_TYPE_LIMIT,
            symbol,
            limit_sell_price,
            target_coin_amount,
        )
        logging.info(
            "current price: %f;  limit sell price: %f;  order_id: %s",
            cur_price,
            limit_sell_price,
            order_id,
        )

    def run(self):
        """ run """
        while True:
            tick_start = datetime.datetime.now()
            logging.info(
                "%s tick start......................................", tick_start
            )
            if self.debug_flag:
                self.on_tick()
            else:
                try:
                    self.on_tick()
                except Exception as ept:
                    logging.critical(ept)
            tick_end = datetime.datetime.now()
            logging.info(
                "%s tick end...; tick  cost: %s -----------------------\n\n",
                tick_end,
                tick_end - tick_start,
            )
            time.sleep(self.config["sec"])
