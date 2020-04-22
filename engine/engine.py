#!/usr/bin/python
"""运行环境引擎"""
import matplotlib.pyplot as plt
import matplotlib.dates as dts
from matplotlib import gridspec
import mpl_finance as mpf
import pandas as pd
import talib
from datetime import datetime,timedelta
import common.log as log
import utils.tools as ts
import utils.indicator as ic
import common.xquant as xq
import common.bill as bl
from db.mongodb import get_mongodb
from setup import *


class Engine:
    """引擎"""

    def __init__(self, instance_id, config, value, db_orders_name=None):
        self.instance_id = instance_id
        self.config = config
        self.value = value

        self.td_db = get_mongodb(db_order_name)

        if db_orders_name:
            self.db_orders_name = db_orders_name
            self.td_db.ensure_index(db_orders_name, [("instance_id",1),("symbol",1)])

        self.can_open_long_time = None
        self.can_open_short_time = None

        self.tp_cc = {"base_open": 0}

        #self.kline_interval = config["kline"]["interval"]


    def log_info(self, info):
        log.info(info)

    def log_warning(self, info):
        log.warngin(info)

    def log_error(self, info):
        log.error(info)

    def log_critical(self, info):
        log.critical(info)

    def log_debug(self, info):
        log.debug(info)


    def get_floating_profit(self, direction, amount, value, commission, cur_price):
        if direction == bl.DIRECTION_LONG:
            cycle_profit = cur_price * amount + value
        else:
            cycle_profit = value - cur_price * amount

        cycle_profit -= commission

        return cycle_profit

    def _get_position(self, symbol, orders, cur_price):
        target_coin, base_coin = xq.get_symbol_coins(symbol)

        info = self._get_position_from_orders(symbol, orders)

        total_profit = info["history_profit"]
        if info["amount"] > 0:
            cycle_profit = self.get_floating_profit(info["direction"], info["amount"], info["value"], info["commission"], cur_price)
            total_profit += cycle_profit

            open_value = self.value
            if self.config["mode"] == 1:
                open_value += info["history_profit"]

            info["floating_profit"] = cycle_profit
            info["floating_profit_rate"] = cycle_profit / open_value

        if orders:
            info["pst_rate"] = orders[-1]["pst_rate"]

        sub_info1 = "amount: %f,  price: %g, cost price: %g,  value: %g,  commission: %g,  limit: %g,  profit: %g," % (
            info["amount"], info["price"], info["cost_price"], info["value"], info["commission"], self.value, info["floating_profit"]) if info["amount"] else ""
        sub_info2 = "  profit rate: %g," % (info["floating_profit_rate"]) if info["value"] else ""
        sub_info3 = "  start_time: %s\n," % info["start_time"].strftime("%Y-%m-%d %H:%M:%S") if "start_time" in info and info["start_time"] else ""
        sub_info4 = "  history_profit: %g,  history_commission: %g,  history_profit_rate: %g," % (
            info["history_profit"], info["history_commission"], (info["history_profit"] / self.value))

        self.log_info(
            "symbol( %s ); current price( %g ); position(%s%s%s%s  total_profit_rate: %g)" % (
            symbol, cur_price, sub_info1, sub_info2, sub_info3, sub_info4, (total_profit / self.value))
        )
        # print(info)
        return info

    def risk_control(self, position_info, cur_price):
        """ 风控 """
        if position_info["amount"] == 0:
            return []

        sl_bills = self.stop_loss(position_info, cur_price)
        tp_bills = self.take_profit(position_info, cur_price)
        return sl_bills + tp_bills

    def get_rates(self, position_info, cur_price):
        pst_price = position_info["price"]
        if position_info["direction"] == bl.DIRECTION_LONG:
            top_rate = (position_info["high"] / pst_price) - 1
            cur_rate = (cur_price / pst_price) - 1
        else:
            top_rate = 1 - (position_info["low"] / pst_price)
            cur_rate = 1 - (cur_price / pst_price)
        return top_rate, cur_rate

    def get_can_open_time(self, cfg):
        next_open_time_cfg_name = "n_o_t"
        delay_timedelta_cfg_name = "d_td"

        if next_open_time_cfg_name in cfg:
            _t1 = xq.get_next_open_time(cfg[next_open_time_cfg_name], self.now())
        else:
            _t1 = None

        if delay_timedelta_cfg_name in cfg:
            _t2 = self.now() + xq.get_interval_timedelta(cfg[delay_timedelta_cfg_name])
        else:
            _t2 = None

        if _t1 and _t2:
            return max(_t1, _t2)

        if _t1:
            return _t1
        elif _t2:
            return _t2
        else:
            return None

    def stop_loss(self, position_info, cur_price):
        """ 止损 """
        sl_bills = []
        # 风控第一条：亏损金额超过额度的10%，如额度1000，亏损金额超过100即刻清仓
        limit_mode = self.config["mode"]
        limit_value = self.value
        if limit_mode == 0:
            pass
        elif limit_mode == 1:
            limit_value += position_info["history_profit"]
        else:
            self.log_error("请选择额度模式，默认是0")

        sl_cfg = self.config["risk_control"]["stop_loss"]
        #sl_t = xq.get_next_open_time(self.kline_interval, self.now())
        sl_t = self.now() + max(xq.get_next_open_timedelta(xq.KLINE_INTERVAL_1DAY, self.now()), timedelta(hours=4))
        if "base_value" in sl_cfg and sl_cfg["base_value"] > 0 and limit_value * sl_cfg["base_value"] + position_info["floating_profit"] <= 0:
            sl_bills.append(bl.create_bill(position_info["direction"], bl.CLOSE_POSITION, 0, "stop loss", "亏损金额超过额度的{:8.2%}".format(sl_cfg["base_value"]), sl_t))

        # 风控第二条：当前价格低于持仓均价的90%，即刻清仓
        pst_price = position_info["price"]
        if position_info["direction"] == bl.DIRECTION_LONG:
            loss_rate = 1 - (cur_price / pst_price)
        else:
            loss_rate = (cur_price / pst_price) - 1
        if pst_price > 0 and "base_price" in sl_cfg and sl_cfg["base_price"] > 0 and loss_rate  >= sl_cfg["base_price"]:
            sl_bills.append(bl.create_bill(position_info["direction"], bl.CLOSE_POSITION, 0, "stop loss", "下跌了持仓均价的{:8.2%}".format(sl_cfg["base_price"]), sl_t))

        stop_loss_price = position_info["stop_loss_price"]
        if stop_loss_price:
            if (position_info["direction"] == bl.DIRECTION_LONG and cur_price <= stop_loss_price) or (position_info["direction"] == bl.DIRECTION_SHORT and cur_price >= stop_loss_price):
                sl_bills.append(bl.create_bill(position_info["direction"], bl.CLOSE_POSITION, 0, "stop loss", "到达指定的止损价格: %f" % (stop_loss_price)))

        top_rate, cur_rate = self.get_rates(position_info, cur_price)

        next_open_time_cfg_name = "n_o_t"
        delay_timedelta_cfg_name = "d_td"
        if "defalut" in sl_cfg:
            d_sl_cfg = sl_cfg["defalut"]
        else:
            # 强制默认
            #d_sl_cfg = {"r": -0.1, next_open_time_cfg_name: "1d", delay_timedelta_cfg_name: "4h"}
            d_sl_cfg = {"r": -0.1}

        defalut_slr = d_sl_cfg["r"]
        if cur_rate <= defalut_slr:
            default_sl_t = self.get_can_open_time(d_sl_cfg)
            sl_bills.append(bl.create_bill(position_info["direction"], bl.CLOSE_POSITION, 0, "defalut stop loss", "到达默认的止损点{:8.2%}".format(defalut_slr), default_sl_t))

        for csl in sl_cfg["condition"]:
            if top_rate >= csl["c"] and cur_rate < csl["r"]:
                c_sl_t = self.get_can_open_time(csl)
                sl_bills.append(bl.create_bill(position_info["direction"], bl.CLOSE_POSITION, 0, "condition stop loss", "到达条件止损点{:8.2%}".format(csl["r"]), c_sl_t))

        return sl_bills

    def take_profit(self, position_info, cur_price):
        """ 止盈 """
        tp_bills = []

        if "high" not in position_info:
            return tp_bills

        tp_cfg = self.config["risk_control"]["take_profit"]

        top_rate, cur_rate = self.get_rates(position_info, cur_price)
        fall_rate = top_rate - cur_rate

        if "base_open" in tp_cfg:
            for bo_band in tp_cfg["base_open"]:
                if top_rate > bo_band[0]:
                    self.log_info("base_open tp_cc 1 = %s" % self.tp_cc["base_open"])
                    if fall_rate >= bo_band[1]:
                        self.tp_cc["base_open"] += 1
                        self.log_info("base_open tp_cc 2 = %s" % self.tp_cc["base_open"])
                        if self.tp_cc["base_open"] >= 1 :
                            tp_bills.append(bl.create_bill(position_info["direction"], bl.CLOSE_POSITION, 0, "take profit", "盈利回落(基于持仓价)  fall rate:{:8.2%} ( {:8.2%}, {:8.2%} )".format(fall_rate, bo_band[0], bo_band[1])))
                    else:
                        self.tp_cc["base_open"] = 0

                    break

        if position_info["direction"] == bl.DIRECTION_LONG:
            price_rate = cur_price / position_info["high"]
        else:
            price_rate = position_info["low"] / cur_price
        if "base_high" in tp_cfg and tp_cfg["base_high"] > 0 and price_rate < (1 - tp_cfg["base_high"]):
            tp_bills.append(bl.create_bill(position_info["direction"], bl.CLOSE_POSITION, 0, "take profit", "盈利回落，基于最高价的{:8.2%}".format(tp_cfg["base_high"])))

        return tp_bills
        """
            if position_info["amount"] > 0:
        today_fall_rate = ts.cacl_today_fall_rate(klines, cur_price)
        if today_fall_rate > 0.1:
            # 清仓卖出
            check_signals.append(
                bl.create_bill(xq.SIDE_SELL, 0, "平仓：当前价距离当天最高价回落10%")
            )

        period_start_time = position_info["start_time"]
        period_fall_rate = ts.cacl_period_fall_rate(
            klines, period_start_time, cur_price
        )
        if period_fall_rate > 0.1:
            # 清仓卖出
            check_signals.append(
                bl.create_bill(xq.SIDE_SELL, 0, "平仓：当前价距离周期内最高价回落10%")
            )
        elif period_fall_rate > 0.05:
            # 减仓一半
            check_signals.append(
                bl.create_bill(xq.SIDE_SELL, 0.5, "减仓：当前价距离周期内最高价回落5%")
            )
        """

    def handle_order(self, symbol, position_info, cur_price, check_bills):
        """ 处理委托 """
        rc_bills = self.risk_control(position_info, cur_price)
        bills = rc_bills + check_bills
        if not bills:
            return
        for bill in bills:
            self.log_info("bill(%r)" % bill["describe"])

        ds_bill = bl.decision_bills(bills)
        self.log_info(
            "decision bill (%s  %s), position rate(%g), describe(%s), can buy after(%s), stop_loss_price(%s)" % (
            ds_bill["direction"],
            ds_bill["action"],
            ds_bill["pst_rate"],
            ds_bill["describe"],
            ds_bill["can_open_time"],
            ds_bill["stop_loss_price"]
            )
        )

        if ds_bill["action"] is None:
            return

        # 限定的时间范围内，不能开仓
        if ds_bill["action"] == bl.OPEN_POSITION:
            if ds_bill["direction"] == bl.DIRECTION_LONG:
                if self.can_open_long_time and self.now() <= self.can_open_long_time:
                        return
            else:
                if self.can_open_short_time and self.now() <= self.can_open_short_time:
                        return

        can_open_time_info = ""
        can_open_time = ds_bill["can_open_time"]
        if can_open_time:
            if ds_bill["direction"] == bl.DIRECTION_LONG:
                if not self.can_open_long_time or self.can_open_long_time < can_open_time:
                    self.can_open_long_time = can_open_time
                    can_open_time_info = "can open long time: %s" % self.can_open_long_time
            else:
                if not self.can_open_short_time or self.can_open_short_time < can_open_time:
                    self.can_open_short_time = can_open_time
                    can_open_time_info = "can open short time: %s" % self.can_open_short_time
            self.log_info(can_open_time_info)

        if ds_bill["pst_rate"] > 1 or ds_bill["pst_rate"] < 0:
            self.log_warning("仓位率（%g）超出范围（0 ~ 1）" % ds_bill["pst_rate"])
            return

        order_rmk = ds_bill["describe"] + ":  " + ds_bill["rmk"]
        rmk = "%s, time: %s,  %s" % (order_rmk, ds_bill["can_open_time"], can_open_time_info) if (ds_bill["can_open_time"] or can_open_time_info) else "%s" % (order_rmk)
        self.send_order(symbol, position_info, cur_price, ds_bill["direction"], ds_bill["action"], ds_bill["pst_rate"], ds_bill["stop_loss_price"], rmk)

    def send_order(self, symbol, position_info, cur_price, direction, action, pst_rate, stop_loss_price, rmk):
        limit_price_rate = self.config["limit_price_rate"]
        limit_mode = self.config["mode"]
        limit_value = self.value
        if limit_mode == 0:
            pass
        elif limit_mode == 1:
            limit_value += position_info["history_profit"]
        else:
            self.log_error("请选择额度模式，默认是0")

        target_coin, base_coin = xq.get_symbol_coins(symbol)

        if action == bl.OPEN_POSITION:
            # 开仓
            if "pst_rate" in position_info and position_info["pst_rate"] >= pst_rate:
                return

            pst_cost = abs(position_info["value"]) + position_info["commission"]
            base_amount = limit_value * pst_rate - pst_cost
            if base_amount <= 0:
                return

            if direction == bl.DIRECTION_LONG:
                # 做多开仓
                base_balance = self.get_balances(base_coin)
                self.log_info("base   balance:  %s" % base_balance)
                base_amount = min(xq.get_balance_free(base_balance), base_amount)
                self.log_info("base_amount: %g" % base_amount)
                if base_amount <= 0:  #
                    return
                target_amount = base_amount / (cur_price * (1 + self.config["commission_rate"]))
                rate = 1 + limit_price_rate["open"]
            else:
                # 做空开仓
                target_balance = self.get_balances(target_coin)
                self.log_info("target balance:  %s" % target_balance)
                # target_amount = min(xq.get_balance_free(target_balance), base_amount / cur_price)
                target_amount = base_amount / cur_price
                self.log_info("target_amount: %g" % target_amount)
                if target_amount <= 0:  #
                    return
                rate = 1 - limit_price_rate["open"]
        else:
            # 平仓
            if (not "pst_rate" in position_info) or position_info["pst_rate"] <= pst_rate:
                return

            target_amount = abs(position_info["amount"]) * (position_info["pst_rate"] - pst_rate) / position_info["pst_rate"]

            if direction == bl.DIRECTION_LONG:
                # 做多平仓
                rate = 1 - limit_price_rate["close"]
            else:
                # 做空平仓
                rate = 1 + limit_price_rate["close"]

        target_amount = ts.reserve_float(target_amount, self.config["digits"][target_coin])
        self.log_info("%s %s target amount: %g" % (direction, action, target_amount))
        if target_amount <= 0:
            return
        limit_price = ts.reserve_float(cur_price * rate, self.config["digits"][base_coin])
        order_id = self.send_order_limit(
            direction,
            action,
            symbol,
            pst_rate,
            cur_price,
            limit_price,
            target_amount,
            stop_loss_price,
            rmk,
        )
        self.log_info(
            "current price: %g;  rate: %g;  order_id: %s" % (cur_price, rate, order_id)
        )

    def check_order(symbol, order):
        if order["direction"] != bl.DIRECTION_LONG and order["direction"] != bl.DIRECTION_SHORT:
            self.log_error("错误的委托方向")
            return False
        if order["action"] != bl.OPEN_POSITION and order["action"] != bl.CLOSE_POSITION:
            self.log_error("错误的委托动作")
            return False
        return True

    def get_order_value(self, order):
        if (order["action"] == bl.OPEN_POSITION and order["direction"] == bl.DIRECTION_LONG) or (order["action"] == bl.CLOSE_POSITION and order["direction"] == bl.DIRECTION_SHORT):
            return - order["deal_value"]
        else:
            return order["deal_value"]

    def get_order_commission(self, order):
        return order["deal_value"] * self.config["commission_rate"]

    def _get_position_from_orders(self, symbol, orders):
        cycle_first_order = None

        history_profit = 0
        history_commission = 0
        cycle_amount = 0
        cycle_value = 0
        cycle_commission = 0
        target_coin, base_coin = xq.get_symbol_coins(symbol)
        for order in orders:
            if not self.check_order(order):
                return None

            if order["action"] == bl.OPEN_POSITION:
                if cycle_amount == 0:
                    cycle_first_order = order
                cycle_amount += order["deal_amount"]
            else:
                cycle_amount -= order["deal_amount"]
            cycle_amount = ts.reserve_float(cycle_amount, self.config["digits"][target_coin])
            cycle_value += self.get_order_value(order)
            cycle_commission += self.get_order_commission(order)

            if cycle_amount == 0:
                history_profit += cycle_value - cycle_commission
                history_commission += cycle_commission
                cycle_value = 0
                cycle_commission = 0

        # 持仓信息
        pst_info = {
            "amount": cycle_amount,  # 数量
            "value": cycle_value,  # 金额
            "commission": cycle_commission,  # 佣金
            "history_profit": history_profit,  # 历史利润
            "history_commission": history_commission,  # 历史佣金
        }

        if cycle_amount > 0:
            pst_info["price"] = abs(cycle_value) / cycle_amount

            if cycle_first_order["direction"] == bl.DIRECTION_LONG:
                pst_info["cost_price"] = (abs(cycle_value) + cycle_commission) / cycle_amount
            else:
                pst_info["cost_price"] = (abs(cycle_value) - cycle_commission) / cycle_amount

            pst_info["stop_loss_price"] = cycle_first_order["stop_loss_price"]

            pst_info["direction"] = cycle_first_order["direction"]
            pst_info["start_time"] = datetime.fromtimestamp(cycle_first_order["create_time"])
            if "high" in order:
                pst_info["high"] = cycle_first_order["high"]
                pst_info["high_time"] = datetime.fromtimestamp(cycle_first_order["high_time"])
                pst_info["low"] = cycle_first_order["low"]
                pst_info["low_time"] = datetime.fromtimestamp(cycle_first_order["low_time"])

        return pst_info


    def stat_orders(self, symbol, orders):
        cycle_id = 1

        history_profit = 0
        history_commission = 0
        cycle_amount = 0
        cycle_value = 0
        cycle_commission = 0
        target_coin, base_coin = xq.get_symbol_coins(symbol)
        for order in orders:
            if not self.check_order(order):
                return None

            order["cycle_id"] = cycle_id

            if order["action"] == bl.OPEN_POSITION:
                cycle_amount += order["deal_amount"]
            else:
                cycle_amount -= order["deal_amount"]
            cycle_amount = ts.reserve_float(cycle_amount, self.config["digits"][target_coin])
            cycle_value += self.get_order_value(order)
            cycle_commission += self.get_order_commission(order)

            deal_price = order["deal_value"] / order["deal_amount"]
            cycle_profit = self.get_floating_profit(order["direction"], cycle_amount, cycle_value, cycle_commission, deal_price)
            order["floating_profit"] = cycle_profit
            order["history_profit"] = history_profit
            order["total_profit"] = cycle_profit + history_profit

            open_value = self.value
            if self.config["mode"] == 1:
                open_value += history_profit
            order["floating_profit_rate"] = order["floating_profit"] / open_value
            order["history_profit_rate"] = order["history_profit"] / self.value
            order["total_profit_rate"] = order["total_profit"] / self.value

            if cycle_amount == 0:
                history_profit += cycle_profit
                history_commission += cycle_commission
                cycle_value = 0
                cycle_commission = 0
                cycle_id += 1

        return orders


    def analyze(self, symbol, orders):
        if len(orders) == 0:
            return

        orders = self.stat_orders(symbol, orders)

        print_switch_hl = True
        print_switch_deal = False
        print_switch_commission = False
        print_switch_profit = False

        title = " id"
        title += "        profit_rate"
        title += "          create_time  price"

        if print_switch_hl:
            title += "  (                                         )"
        title += "                   pst_rate"

        if print_switch_deal:
            title += "  deal_amount  deal_value"
        if print_switch_commission:
            title += "  total_commission"
        if print_switch_profit:
            title += "        profit(total)"
        title += "  rmk"
        print(title)

        total_commission = 0
        for index ,order in enumerate(orders):
            commission = order["deal_value"] * self.config["commission_rate"]
            total_commission += commission

            order["trade_time"] = datetime.fromtimestamp(order["create_time"])

            info = "%3d" % (index)
            info += "  {:7.2%}({:8.2%})".format(
                order["floating_profit_rate"], order["total_profit_rate"]
            )
            info += "  %s  %10g" % (
                    datetime.fromtimestamp(order["create_time"]),
                    order["deal_value"]/order["deal_amount"],
                )

            if print_switch_hl:
                total_commission_rate = 0 # 2 * self.config["commission_rate"]
                if "high" in order:
                    deal_price = order["deal_value"]/order["deal_amount"]
                    if order["direction"] == bl.DIRECTION_LONG:
                        tmp_profit_rate = order["high"] / deal_price - 1 - total_commission_rate
                    else:
                        tmp_profit_rate = 1 - order["high"] / deal_price - total_commission_rate

                    info += "  ({:8.2%}".format(tmp_profit_rate)
                    info += "  %10g, %s)" % (order["high"], datetime.fromtimestamp(order["high_time"]))
                else:
                    pre_deal_price = pre_order["deal_value"]/pre_order["deal_amount"]
                    if order["direction"] == bl.DIRECTION_LONG:
                        tmp_profit_rate = pre_order["low"] / pre_deal_price - 1 - total_commission_rate
                    else:
                        tmp_profit_rate = 1 - pre_order["low"] / pre_deal_price - total_commission_rate
                    info += "  ({:8.2%}".format(tmp_profit_rate)
                    info += "  %10g, %s)" % (pre_order["low"], datetime.fromtimestamp(pre_order["low_time"]))

            info += "  %s,%5s" % (
                    order["direction"],
                    order["action"],
                )
            info += "  {:8.2f}".format(order["pst_rate"])

            if print_switch_deal:
                info += "  %11g  %10g" % (
                        order["deal_amount"],
                        order["deal_value"],
                    )
            if print_switch_commission:
                info += "  %16g" % (
                        total_commission,
                    )
            if print_switch_profit:
                info += "  {:8.2f}({:9.2f})".format(
                        order["floating_profit"],
                        order["total_profit"],
                    )
            info += "  %s" % (order["rmk"])

            pre_order = order
            print(info)

        orders_df = pd.DataFrame(orders)

        orders_df["create_time"] = orders_df["create_time"].map(lambda x: datetime.fromtimestamp(x))
        orders_df["deal_price"] = orders_df["deal_value"] / orders_df["deal_amount"]
        orders_df["commission"] = orders_df["deal_value"] * self.config["commission_rate"]


        orders_df["signal_id"] = orders_df["rmk"].map(lambda x: x.split(":  ")[0])
        orders_df["signal_rmk"] = orders_df["rmk"].map(lambda x: x.split(":  ")[1])
        del orders_df["order_id"]
        del orders_df["instance_id"]
        del orders_df["rmk"]
        #print(orders_df)
        self.stat("total", orders_df)

        orders_df = orders_df.sort_values(by=['signal_id'])
        for signal_id in orders_df["signal_id"].drop_duplicates().values:
            #print(signal_id)

            cycle_ids = orders_df[(orders_df["signal_id"]==signal_id)]["cycle_id"]
            #print(cycle_ids)

            self.stat(signal_id, orders_df[(orders_df["cycle_id"].isin(cycle_ids))] )


    def calc(self, symbol, orders):
        if len(orders) <= 0:
            return 0, 0, 0, 0
        orders_df = pd.DataFrame(self.calc_order(symbol, orders))
        close_df = orders_df[(orders_df["action"]==bl.CLOSE_POSITION)]

        win_df = close_df[(close_df["floating_profit_rate"] > 0)]
        loss_df =close_df[(close_df["floating_profit_rate"] < 0)]
        win_count = len(win_df)
        loss_count = len(loss_df)

        total_profit_rate = close_df["floating_profit"].sum() / self.value
        sum_profit_rate = close_df["floating_profit_rate"].sum()
        return round(total_profit_rate, 4), round(sum_profit_rate, 4), win_count, loss_count


    def stat(self, signal_id, orders_df):
        print("\n signal: " + signal_id)
        win_df = orders_df[(orders_df["action"]==bl.CLOSE_POSITION) & (orders_df["floating_profit_rate"] > 0)]
        loss_df =orders_df[(orders_df["action"]==bl.CLOSE_POSITION) & (orders_df["floating_profit_rate"] < 0)]

        win_count = len(win_df)
        fail_count = len(loss_df)
        if win_count > 0 or fail_count > 0:
            win_rate = win_count / (win_count + fail_count)
        else:
            win_rate = 0
        print("win count: %g, loss count: %g, win rate: %4.2f%%" % (win_count, fail_count, round(win_rate*100, 2)))

        w_profit_rates = win_df["floating_profit_rate"]
        l_profit_rates = loss_df["floating_profit_rate"]
        print("profit rate(total: %6.2f%%, max: %6.2f%%, min: %6.2f%%, average: %6.2f%%)" % (round(w_profit_rates.sum()*100, 2), round(w_profit_rates.max()*100, 2), round(w_profit_rates.min()*100, 2), round(w_profit_rates.mean()*100, 2)))
        print("loss   rate(total: %6.2f%%, max: %6.2f%%, min: %6.2f%%, average: %6.2f%%)" % (round(l_profit_rates.sum()*100, 2), round(l_profit_rates.min()*100, 2), round(l_profit_rates.max()*100, 2), round(l_profit_rates.mean()*100, 2)))

        if fail_count > 0:
            kelly = win_rate - (1-win_rate)/(w_profit_rates.mean()/abs(l_profit_rates.mean()))
        else:
            kelly = win_rate
        print("Kelly Criterion: %.2f%%" % round(kelly*100, 2))


    def display(self, symbol, orders, klines, display_count):
        os_keys = ts.parse_ic_keys("EMA,ATR")
        disp_ic_keys = ts.parse_ic_keys("macd,rsi")

        for index, value in enumerate(self.md.kline_column_names):
            if value == "high":
                highindex = index
            if value == "low":
                lowindex = index
            if value == "open":
                openindex = index
            if value == "close":
                closeindex = index
            if value == "volume":
                volumeindex = index
            if value == "open_time":
                opentimeindex = index

        klines_df = pd.DataFrame(klines, columns=self.md.kline_column_names)

        atrs = talib.ATR(klines_df["high"], klines_df["low"], klines_df["close"], timeperiod=14)
        natrs = talib.NATR(klines_df["high"], klines_df["low"], klines_df["close"], timeperiod=14)
        tranges = talib.TRANGE(klines_df["high"], klines_df["low"], klines_df["close"])

        e_p  = 26
        emas = talib.EMA(klines_df["close"], timeperiod=e_p)
        s_emas = talib.EMA(klines_df["close"], timeperiod=e_p/2)
        t_emas = talib.EMA(klines_df["close"], timeperiod=30)

        demas = talib.DEMA(klines_df["close"], timeperiod=30)

        ks, ds, js = ic.pd_kdj(klines_df)

        klines_df = ic.pd_macd(klines_df)
        difs = [round(a, 2) for a in klines_df["dif"]]
        deas = [round(a, 2) for a in klines_df["dea"]]
        macds = [round(a, 2) for a in klines_df["macd"]]
        difs = difs[-display_count:]
        deas = deas[-display_count:]
        macds = macds[-display_count:]

        # display
        atrs = atrs[-display_count:]
        natrs = natrs[-display_count:]
        tranges = tranges[-display_count:]
        #ads = ads[-display_count:]
        emas = emas[-display_count:]
        s_emas = s_emas[-display_count:]
        t_emas = t_emas[-display_count:]
        demas = demas[-display_count:]
        ks = ks[-display_count:]
        ds = ds[-display_count:]
        js = js[-display_count:]


        opens = klines_df["open"][-display_count:]
        closes = klines_df["close"][-display_count:]
        opens = pd.to_numeric(opens)
        closes = pd.to_numeric(closes)
        base_close = closes.values[0]

        open_times = [datetime.fromtimestamp((float(open_time)/1000)) for open_time in klines_df["open_time"][-display_count:]]
        close_times = [datetime.fromtimestamp((float(close_time)/1000)) for close_time in klines_df["close_time"][-display_count:]]
        """
        gs = gridspec.GridSpec(8, 1)
        gs.update(left=0.04, bottom=0.04, right=1, top=1, wspace=0, hspace=0)
        axes = [
            plt.subplot(gs[0:-2, :]),
            #plt.subplot(gs[-4:-2, :]),
            plt.subplot(gs[-2:-1, :]),
            plt.subplot(gs[-1, :])
        ]
        """
        fig, axes = plt.subplots(len(disp_ic_keys)+2, 1, sharex=True)
        fig.subplots_adjust(left=0.04, bottom=0.04, right=1, top=1, wspace=0, hspace=0)

        trade_times = [order["trade_time"] for order in orders]

        quotes = []
        for k in klines[-display_count:]:
            d = datetime.fromtimestamp(k[0]/1000)
            quote = (dts.date2num(d), float(k[1]), float(k[4]), float(k[2]), float(k[3]))
            quotes.append(quote)

        i = -1
        i += 1
        mpf.candlestick_ochl(axes[i], quotes, width=0.02, colorup='g', colordown='r')
        axes[i].set_ylabel(symbol + '  ' + self.config['kline']['interval'])
        axes[i].grid(True)
        axes[i].autoscale_view()
        axes[i].xaxis_date()
        axes[i].plot(trade_times, [(order["deal_value"] / order["deal_amount"]) for order in orders], "o--")

        os_key = 'EMA'
        if os_key in os_keys:
            axes[i].plot(close_times, emas, "b--", label="%sEMA" % (e_p))
            axes[i].plot(close_times, s_emas, "c--", label="%sEMA" % (e_p/2))
            axes[i].plot(close_times, t_emas, "m--", label="%sEMA" % (30))

        os_key = 'DEMA'
        if os_key in os_keys:
            real = talib.DEMA(klines_df["close"], timeperiod=30)
            ts.ax(axes[i], os_key, close_times, real[-display_count:], "y")

        os_key = 'ATR'
        if os_key in os_keys:
            axes[i].plot(close_times, emas + atrs, "y--", label="1ATR")
            axes[i].plot(close_times, emas - atrs, "y--", label="1ATR")

            #axes[i].plot(close_times, s_emas + atrs, "m--", label="1ATR")
            #axes[i].plot(close_times, demas + atrs, "b--", label="1ATR")



            axes[i].plot(close_times, emas + 2*atrs, "y--", label="2ATR")
            axes[i].plot(close_times, emas - 2*atrs, "y--", label="2ATR")
            #axes[i].plot(close_times, emas + 3*atrs, "y--", label="3ATR")
            #axes[i].plot(close_times, emas - 3*atrs, "y--", label="3ATR")

            #axes[i].plot(close_times, emas + 4*atrs, "m--", label="4ATR")
            #axes[i].plot(close_times, emas - 4*atrs, "m--", label="4ATR")
            #axes[i].plot(close_times, emas + 5*atrs, "m--", label="5ATR")
            #axes[i].plot(close_times, emas - 5*atrs, "m--", label="5ATR")
            ats = 6
            label = "%d ATR" % (ats)
            #axes[i].plot(close_times, emas + ts*atrs, "m--", label="6ATR")
            #axes[i].plot(close_times, emas - ts*atrs, "m--", label="6ATR")

            ats = 12
            label = "%d ATR" % (ats)
            #axes[i].plot(close_times, emas + ts*atrs, "g--", label=label)
            #axes[i].plot(close_times, emas - ts*atrs, "g--", label=label)

        ic_key = 'mr'
        if ic_key in disp_ic_keys:
            i += 1
            mrs = [round(a, 4) for a in (klines_df["macd"][-display_count:] / closes)]
            mrs = mrs[-display_count:]
            axes[i].set_ylabel('mr')
            axes[i].grid(True)
            axes[i].plot(close_times, mrs, "r--", label="mr")

            leam_mrs = klines_df["macd"] / emas
            seam_mrs = klines_df["macd"] / s_emas
            leam_mrs = leam_mrs[-display_count:]
            seam_mrs = seam_mrs[-display_count:]
            axes[i].plot(close_times, leam_mrs, "y--", label="leam_mr")
            axes[i].plot(close_times, seam_mrs, "m--", label="seam_mr")

        ic_key = 'difr'
        if ic_key in disp_ic_keys:
            i += 1
            difrs = [round(a, 2) for a in (klines_df["dif"][-display_count:] / closes)]
            dears = [round(a, 2) for a in (klines_df["dea"][-display_count:] / closes)]
            difrs = difrs[-display_count:]
            dears = dears[-display_count:]
            axes[i].set_ylabel('r')
            axes[i].grid(True)
            axes[i].plot(close_times, difrs, "m--", label="difr")
            axes[i].plot(close_times, dears, "m--", label="dear")

        ic_key = 'macd'
        if ic_key in disp_ic_keys:
            i += 1
            axes[i].set_ylabel('macd')
            axes[i].grid(True)
            axes[i].plot(close_times, difs, "y", label="dif")
            axes[i].plot(close_times, deas, "b", label="dea")
            axes[i].plot(close_times, macds, "r", drawstyle="steps", label="macd")

        ic_key = 'rsi'
        if ic_key in disp_ic_keys:
            i += 1
            axes[i].set_ylabel('rsi')
            axes[i].grid(True)
            rsis = talib.RSI(klines_df["close"], timeperiod=14)
            rsis = [round(a, 3) for a in rsis][-display_count:]
            axes[i].plot(close_times, rsis, "r", label="rsi")
            axes[i].plot(close_times, [70]*len(rsis), '-', color='r')
            axes[i].plot(close_times, [30]*len(rsis), '-', color='r')

            """
            rs2 = ic.py_rsis(klines, closeindex, period=14)
            rs2 = [round(a, 3) for a in rs2][-display_count:]
            axes[i].plot(close_times, rs2, "y", label="rsi2")

            rs3 = ic.py_rsis2(klines, closeindex, period=14)
            rs3 = [round(a, 3) for a in rs3][-display_count:]
            axes[i].plot(close_times, rs3, "m", label="rsi3")
            """

        ic_key = 'AD'
        if ic_key in disp_ic_keys:
            ads = talib.AD(klines_df["high"], klines_df["low"], klines_df["close"], klines_df["volume"])
            i += 1
            axes[i].set_ylabel(ic_key)
            axes[i].grid(True)
            axes[i].plot(close_times, ads, "y:", label=ic_key)

        ic_key = 'DX'
        if ic_key in disp_ic_keys:
            dxs = talib.DX(klines_df["high"], klines_df["low"], klines_df["close"], timeperiod=14)
            dxs = dxs[-display_count:]
            adxs = talib.ADX(klines_df["high"], klines_df["low"], klines_df["close"], timeperiod=14)
            adxs = adxs[-display_count:]
            adxrs = talib.ADXR(klines_df["high"], klines_df["low"], klines_df["close"], timeperiod=14)
            adxrs = adxrs[-display_count:]
            i += 1
            ts.ax(axes[i], ic_key, close_times, dxs, "r:")
            ts.ax(axes[i], ic_key, close_times, adxs, "y:")
            ts.ax(axes[i], ic_key, close_times, adxrs, "k:")

        ic_key = 'PLUS_DM'
        if ic_key in disp_ic_keys:
            real = talib.PLUS_DM(klines_df["high"], klines_df["low"])
            i += 1
            axes[i].set_ylabel(ic_key)
            axes[i].grid(True)
            axes[i].plot(close_times, real[-display_count:], "y:", label=ic_key)

        ic_key = 'MINUS_DM'
        if ic_key in disp_ic_keys:
            real = talib.MINUS_DM(klines_df["high"], klines_df["low"])
            i += 1
            axes[i].set_ylabel(ic_key)
            axes[i].grid(True)
            axes[i].plot(close_times, real[-display_count:], "y:", label=ic_key)

        ic_key = 'volatility'
        if ic_key in disp_ic_keys:
            i += 1
            axes[i].set_ylabel('volatility')
            axes[i].grid(True)
            axes[i].plot(close_times, atrs, "y:", label="ATR")
            axes[i].plot(close_times, natrs, "k--", label="NATR")
            axes[i].plot(close_times, tranges, "c--", label="TRANGE")

        ic_key = 'kdj'
        if ic_key in disp_ic_keys:
            i += 1
            axes[i].set_ylabel('kdj')
            axes[i].grid(True)
            axes[i].plot(close_times, ks, "b", label="k")
            axes[i].plot(close_times, ds, "y", label="d")
            axes[i].plot(close_times, js, "m", label="j")

        """
        axes[-2].set_ylabel('rate')
        axes[-2].grid(True)
        #axes[-2].set_label(["position rate", "profit rate"])
        axes[-2].plot(trade_times ,[round(100*order["pst_rate"], 2) for order in orders], "k-", drawstyle="steps-post", label="position")
        axes[-2].plot(trade_times ,[round(100*order["floating_profit_rate"], 2) for order in orders], "g--", drawstyle="steps", label="profit")
        """

        axes[-1].set_ylabel('total profit rate')
        axes[-1].grid(True)
        axes[-1].plot(trade_times, [round(100*order["total_profit_rate"], 2) for order in orders], "go--")
        axes[-1].plot(close_times, [round(100*((close/base_close)-1), 2) for close in closes], "r--")

        """
        trade_times = []
        pst_rates = []
        for i, order in enumerate(orders):
            #补充
            if i > 0 and orders[i-1]["pst_rate"] > 0:
                tmp_trade_date = orders[i-1]["trade_time"].date() + timedelta(days=1)
                while tmp_trade_date < order["trade_time"].date():
                    trade_times.append(tmp_trade_date)
                    pst_rates.append(orders[i-1]["pst_rate"])
                    print("add %s, %s" % (tmp_trade_date, orders[i-1]["pst_rate"]))
                    tmp_trade_date += timedelta(days=1)

            # 添加
            trade_times.append(order["trade_time"])
            pst_rates.append(order["pst_rate"])
            print("%s, %s" % (order["trade_time"], order["pst_rate"]))
        plt.bar(trade_times, pst_rates, width= 0.3) # 
        """

        plt.show()

