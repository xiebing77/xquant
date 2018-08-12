#!/usr/bin/python
"""strategy"""

import datetime
import logging
import uuid
import pandas as pd
from engine.realengine import RealEngine
from engine.backtest import BackTest
import common.xquant as xq
import utils.tools as ts


def create_signal(side, pst_rate, rmk):
    """创建交易信号"""
    return {"side": side, "pst_rate": pst_rate, "rmk": rmk}


def decision_signals(signals):
    """决策交易信号"""
    logging.info("signals(%r)", signals)
    sdf = pd.DataFrame(signals)
    sdf_min = sdf.groupby("side")["pst_rate"].min()

    if xq.SIDE_SELL in sdf_min:
        return xq.SIDE_SELL, sdf_min[xq.SIDE_SELL]

    if xq.SIDE_BUY in sdf_min:
        return xq.SIDE_BUY, sdf_min[xq.SIDE_BUY]

    return None, None


def decision_signals2(signals):
    """决策交易信号"""
    logging.info("signals(%r)", signals)
    if not signals:
        return None, None

    side = None
    for signal in signals:
        new_side = signal["side"]
        new_rate = signal["pst_rate"]
        new_rmk = signal["rmk"]

        if side is None:
            side = new_side
            rate = new_rate
            rmk = new_rmk
        elif side is new_side:
            if rate > new_rate:
                rate = new_rate
                rmk = new_rmk
        else:
            if side is xq.SIDE_BUY:
                side = new_side
                rate = new_rate
                rmk = new_rmk
    logging.info(
        "decision signal side(%s), position rate(%g), rmk(%s)", side, rate, rmk
    )

    return side, rate


class Strategy:
    """Strategy"""

    def __init__(self, strategy_config, engine_config, debug):
        self.config = strategy_config
        self.debug_flag = debug

        self.instance_id = self.__class__.__name__ + "_" + self.config["symbol"] + "_"
        if engine_config["select"] == "real":
            self.instance_id += engine_config["real"]["instance_id"]  # 实盘则暂时由config配置
        else:
            self.instance_id += str(uuid.uuid1())  # 每次回测都是一个独立的实例

        logfilename = (
            self.instance_id + "_" + datetime.datetime.now().strftime("%Y%m%d") + ".log"
        )
        print(logfilename)
        logging.basicConfig(level=logging.NOTSET, filename=logfilename)

        logging.info("strategy name: %s;  config: %s", self.__class__.__name__, self.config)

        if engine_config["select"] == "real":
            self.engine = RealEngine(self.instance_id, engine_config["real"])
        else:
            self.engine = BackTest(self.instance_id, engine_config["backtest"])

    def risk_control(self, position_info, cur_price):
        """ 风控 """
        rc_signals = []

        # 风控第一条：亏损金额超过额度的10%，如额度1000，亏损金额超过100即刻清仓
        limit_mode = self.config["limit"]["mode"]
        limit_value = self.config["limit"]["value"]
        if limit_mode == 0:
            pass
        elif limit_mode == 1:
            limit_value += position_info["history_profit"]
        else:
            logging("请选择额度模式，默认是0")

        loss_limit = limit_value * 0.1
        if loss_limit + position_info["profit"] <= 0:
            rc_signals.append(create_signal(xq.SIDE_SELL, 0, "风控平仓：亏损金额超过额度的10%"))

        # 风控第二条：当前价格低于持仓均价的90%，即刻清仓
        pst_price = position_info["price"]
        if pst_price > 0 and cur_price / pst_price <= 0.9:
            rc_signals.append(create_signal(xq.SIDE_SELL, 0, "风控平仓：当前价低于持仓均价的90%"))

        return rc_signals

    def handle_order(self, symbol, cur_price, position_info, check_signals):
        """ 处理委托 """
        rc_signals = self.risk_control(position_info, cur_price)
        if xq.SIDE_BUY in rc_signals:
            logging.warning("风控方向不能为买")
            return

        if not check_signals and not rc_signals:
            return

        dcs_side, dcs_pst_rate = decision_signals2(rc_signals + check_signals)

        if dcs_side is None:
            return

        if dcs_pst_rate > 1 or dcs_pst_rate < 0:
            logging.warning("仓位率（%g）超出范围（0 ~ 1）", dcs_pst_rate)
            return

        limit_mode = self.config["limit"]["mode"]
        limit_value = self.config["limit"]["value"]
        if limit_mode == 0:
            pass
        elif limit_mode == 1:
            limit_value += position_info["history_profit"]
        else:
            logging("请选择额度模式，默认是0")

        if dcs_side == xq.SIDE_BUY:
            buy_base_amount = (
                limit_value * dcs_pst_rate - position_info["cost"]
            )
            self.limit_buy(symbol, ts.reserve_float(buy_base_amount), cur_price)
        elif dcs_side == xq.SIDE_SELL:
            if position_info["cost"] == 0:
                return
            position_rate = position_info["cost"] / limit_value
            dcs_pst_amount = position_info["amount"] * dcs_pst_rate / position_rate

            target_coin, _ = xq.get_symbol_coins(symbol)
            sell_target_amount = position_info["amount"] - ts.reserve_float(
                dcs_pst_amount, self.config["digits"][target_coin]
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
        logging.info("buy_base_amount: %g", buy_base_amount)

        if buy_base_amount <= 0:  #
            return

        target_amount_digits = self.config["digits"][target_coin]
        buy_target_amount = ts.reserve_float(
            buy_base_amount / cur_price, target_amount_digits
        )
        logging.info("buy target coin amount: %g", buy_target_amount)

        rate = 1.1
        order_id = self.engine.send_order_limit(
            xq.SIDE_BUY,
            symbol,
            cur_price,
            rate,
            self.config["digits"][base_coin],
            buy_target_amount,
        )
        logging.info(
            "current price: %g;  rate: %g;  order_id: %s ", cur_price, rate, order_id
        )
        return

    def limit_sell(self, symbol, target_coin_amount, cur_price):
        """ 限价卖 """
        if target_coin_amount <= 0:
            return
        logging.info("sell target coin num: %g", target_coin_amount)

        rate = 0.9
        _, base_coin = xq.get_symbol_coins(symbol)
        order_id = self.engine.send_order_limit(
            xq.SIDE_SELL,
            symbol,
            cur_price,
            rate,
            self.config["digits"][base_coin],
            target_coin_amount,
        )
        logging.info(
            "current price: %g;  rate: %g;  order_id: %s", cur_price, rate, order_id
        )

    def run(self):
        """ run """
        if self.debug_flag:
            self.engine.run(self)
        else:
            try:
                self.engine.run(self)
            except Exception as ept:
                logging.critical(ept)
