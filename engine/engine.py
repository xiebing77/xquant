#!/usr/bin/python
"""运行环境引擎"""
from datetime import datetime
import logging
import utils.tools as ts
from setup import mongo_user, mongo_pwd, db_name, db_url
import common.xquant as xq
import db.mongodb as md


class Engine:
    """引擎"""

    def __init__(self, instance_id, config, db_orders_name):
        self.instance_id = instance_id
        self.config = config
        self.db_orders_name = db_orders_name
        self._db = md.MongoDB(mongo_user, mongo_pwd, db_name, db_url)

        self.cur_pst = {}

    def _get_position(self, symbol, cur_price):
        info = {
            "amount": 0,  # 数量
            "price": 0,  # 平均价格，不包含佣金
            "cost_price": 0,  # 分摊佣金后的成本价
            "value": 0,  # 金额
            "commission": 0,  # 佣金
            "profit": 0,  # 当前利润
            "history_profit": 0,  # 历史利润
            "start_time": None,  # 本周期第一笔买入时间
        }

        orders = self._db.find(
            self.db_orders_name, {"instance_id": self.instance_id, "symbol": symbol}
        )
        for order in orders:
            deal_amount = order["deal_amount"]
            deal_value = order["deal_value"]
            commission = deal_value * self.config["commission_rate"]

            if order["side"] == xq.SIDE_BUY:
                if info["amount"] == 0:
                    info["start_time"] = datetime.fromtimestamp(order["create_time"])

                info["amount"] += deal_amount
                info["value"] += deal_value
                info["commission"] += commission

            elif order["side"] == xq.SIDE_SELL:
                info["amount"] -= deal_amount
                info["value"] -= deal_value
                info["commission"] += commission
            else:
                logging.error("错误的委托方向")
                continue

            if info["amount"] == 0:
                info["history_profit"] -= (info["value"] + info["commission"])
                info["value"] = 0
                info["commission"] = 0
                info["start_time"] = None

        if info["amount"] == 0:
            pass
        elif info["amount"] > 0:
            info["profit"] = cur_price * info["amount"] - info["value"] - info["commission"]
            info["price"] = info["value"] / info["amount"]
            info["cost_price"] = (info["value"] + info["commission"]) / info["amount"]

        else:
            logging.error("持仓数量不可能小于0")

        info["limit_base_amount"] = self.config["limit"]["value"]

        logging.info(
            "symbol( %s ); current price( %g ); position(%s%s%s  history_profit: %g,  total_profit_rate: %g)",
            symbol,
            cur_price,
            "amount: %g,  price: %g, cost price: %g,  value: %g,  commission: %g,  limit: %g,  profit: %g,"
            % (
                info["amount"],
                info["price"],
                info["cost_price"],
                info["value"],
                info["commission"],
                info["limit_base_amount"],
                info["profit"],
            )
            if info["amount"]
            else "",
            "  profit rate: %g," % (info["profit"] / (info["value"] + info["commission"]))
            if info["value"]
            else "",
            "  start_time: %s\n," % info["start_time"].strftime("%Y-%m-%d %H:%M:%S")
            if info["start_time"]
            else "",
            info["history_profit"],
            (info["profit"] + info["history_profit"]) / info["limit_base_amount"],
        )
        # print(info)
        return info

    def risk_control(self, position_info, cur_price):
        """ 风控，用于止损 """
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
            rc_signals.append(xq.create_signal(xq.SIDE_SELL, 0, "风控平仓：亏损金额超过额度的10%"))

        # 风控第二条：当前价格低于持仓均价的90%，即刻清仓
        pst_price = position_info["price"]
        if pst_price > 0 and cur_price / pst_price <= 0.9:
            rc_signals.append(xq.create_signal(xq.SIDE_SELL, 0, "风控平仓：当前价低于持仓均价的90%"))

        return rc_signals

    '''
    def loss_control():
        """ 用于止盈 """
            if position_info["amount"] > 0:
        today_fall_rate = ts.cacl_today_fall_rate(klines, cur_price)
        if today_fall_rate > 0.1:
            # 清仓卖出
            check_signals.append(
                xq.create_signal(xq.SIDE_SELL, 0, "平仓：当前价距离当天最高价回落10%")
            )

        period_start_time = position_info["start_time"]
        period_fall_rate = ts.cacl_period_fall_rate(
            klines, period_start_time, cur_price
        )
        if period_fall_rate > 0.1:
            # 清仓卖出
            check_signals.append(
                xq.create_signal(xq.SIDE_SELL, 0, "平仓：当前价距离周期内最高价回落10%")
            )
        elif period_fall_rate > 0.05:
            # 减仓一半
            check_signals.append(
                xq.create_signal(xq.SIDE_SELL, 0.5, "减仓：当前价距离周期内最高价回落5%")
            )
    '''


    def handle_order(self, symbol, cur_price, check_signals):
        """ 处理委托 """
        position_info = self.get_position(symbol, cur_price)

        rc_signals = self.risk_control(position_info, cur_price)
        if xq.SIDE_BUY in rc_signals:
            logging.warning("风控方向不能为买")
            return

        if not check_signals and not rc_signals:
            return

        signals = rc_signals + check_signals
        logging.info("signals(%r)", signals)
        dcs_side, dcs_pst_rate, dcs_rmk = xq.decision_signals2(signals)
        logging.info(
            "decision signal side(%s), position rate(%g), rmk(%s)",
            dcs_side,
            dcs_pst_rate,
            dcs_rmk,
        )

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

        if symbol not in self.cur_pst:
            self.cur_pst[symbol] = {"rate":0, "amount":0}

        target_coin, base_coin = xq.get_symbol_coins(symbol)
        if dcs_side == xq.SIDE_BUY:
            logging.info("cur_pst %s: %s", symbol, self.cur_pst[symbol])
            if self.cur_pst[symbol]["rate"] >= dcs_pst_rate:
                return

            buy_base_amount = limit_value * dcs_pst_rate - position_info["value"] - position_info["commission"]
            if buy_base_amount <= 0:
                return

            base_balance = self.get_balances(base_coin)
            logging.info("base   balance:  %s", base_balance)

            buy_base_amount = min(xq.get_balance_free(base_balance), buy_base_amount)
            logging.info("buy_base_amount: %g", buy_base_amount)
            if buy_base_amount <= 0:  #
                return

            buy_target_amount = ts.reserve_float(
                buy_base_amount / (cur_price * (1 + self.config["commission_rate"])),
                self.config["digits"][target_coin],
            )
            logging.info("buy target coin amount: %g", buy_target_amount)

            rate = 1.1
            limit_price = ts.reserve_float(cur_price * rate, self.config["digits"][base_coin])
            order_id = self.send_order_limit(
                xq.SIDE_BUY,
                symbol,
                cur_price,
                limit_price,
                buy_target_amount,
            )
            logging.info(
                "current price: %g;  rate: %g;  order_id: %s ", cur_price, rate, order_id
            )

            self.cur_pst[symbol]["rate"] = dcs_pst_rate
            self.cur_pst[symbol]["amount"]+=buy_target_amount

        elif dcs_side == xq.SIDE_SELL:
            if self.cur_pst[symbol]["rate"] <= dcs_pst_rate:
                return

            sell_target_amount = self.cur_pst[symbol]["amount"] * (self.cur_pst[symbol]["rate"] - dcs_pst_rate) / self.cur_pst[symbol]["rate"]
            logging.info("sell_target_amount     : %g" % sell_target_amount)
            if sell_target_amount <= 0:
                return

            rate = 0.9
            limit_price = ts.reserve_float(cur_price * rate, self.config["digits"][base_coin])
            order_id = self.send_order_limit(
                xq.SIDE_SELL,
                symbol,
                cur_price,
                limit_price,
                sell_target_amount,
            )
            logging.info(
                "current price: %g;  rate: %g;  order_id: %s", cur_price, rate, order_id
            )

            self.cur_pst[symbol]["rate"] = dcs_pst_rate
            self.cur_pst[symbol]["amount"]-=sell_target_amount
        else:
            return
