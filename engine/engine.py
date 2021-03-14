#!/usr/bin/python
"""运行环境引擎"""
import pandas as pd
import talib
from datetime import datetime,timedelta
import common.log as log
import utils.tools as ts
import utils.indicator as ic
import common.xquant as xq
import common.kline as kl
import common.bill as bl
from .order import *
from pprint import pprint


class Engine:
    """引擎"""

    def __init__(self, instance_id, config, value, log_switch):
        self.instance_id = instance_id
        self.config = config
        self.value = value

        self.can_open_long_time = None
        self.can_open_short_time = None

        self.tp_cc = {"base_open": 0}

        self.log_switch = log_switch

        #self.kline_interval = config["kline"]["interval"]


    def log_info(self, info):
        if self.log_switch:
            log.info(info)

    def log_warning(self, info):
        if self.log_switch:
            log.warngin(info)

    def log_error(self, info):
        if self.log_switch:
            log.error(info)

    def log_critical(self, info):
        if self.log_switch:
            log.critical(info)

    def log_debug(self, info):
        if self.log_switch:
            log.debug(info)


    def _get_position(self, symbol, orders, cur_price):
        target_coin, base_coin = xq.get_symbol_coins(symbol)

        #info = self._get_position_from_orders(symbol, orders)
        info = get_pst_by_orders(orders, self.config["commission_rate"])

        if orders:
            info["pst_rate"] = orders[-1]["pst_rate"]
            pst_first_order = get_pst_first_order(orders)
            info[POSITON_HIGH_KEY]      = pst_first_order[POSITON_HIGH_KEY]
            info[POSITON_HIGH_TIME_KEY] = pst_first_order[POSITON_HIGH_TIME_KEY]
            info[POSITON_LOW_KEY]       = pst_first_order[POSITON_LOW_KEY]
            info[POSITON_LOW_TIME_KEY]  = pst_first_order[POSITON_LOW_TIME_KEY]

        if self.log_switch:
            floating_profit, total_profit, floating_profit_rate, total_profit_rate = get_floating_profit(info, self.value, self.config["mode"], cur_price)

            sub_info1 = "amount: %f,  price: %g, cost price: %g,  value: %g,  commission: %g,  limit: %g,  profit: %g," % (
                info["amount"], info["price"], get_cost_price(info), info["value"], info["commission"], self.value, floating_profit) if info["amount"] else ""
            sub_info2 = "  profit rate: %g%%," % (floating_profit_rate * 100) if info["value"] else ""
            sub_info3 = "  start_time: %s\n," % info["start_time"].strftime("%Y-%m-%d %H:%M:%S") if "start_time" in info and info["start_time"] else ""
            sub_info4 = "  history_profit: %g,  history_commission: %g,  history_profit_rate: %g%%," % (
                info["history_profit"], info["history_commission"], (info["history_profit"] * 100 / self.value))

            self.log_info(
                "symbol( %s ); current price( %g ); position(%s%s%s%s  total_profit_rate: %g%%)" % (
                symbol, cur_price, sub_info1, sub_info2, sub_info3, sub_info4, (total_profit / self.value) * 100)
            )
        # print(info)
        return info

    def risk_control(self, position_info, cur_price):
        """ 风控 """
        if position_info["amount"] == 0 or pst_is_lock(position_info):
            return []

        sl_bills = self.stop_loss(position_info, cur_price)
        tp_bills = self.take_profit(position_info, cur_price)
        return sl_bills + tp_bills

    def get_rates(self, position_info, cur_price):
        pst_price = get_cost_price(position_info)
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
            _t1 = kl.get_next_open_time(cfg[next_open_time_cfg_name], self.now())
        else:
            _t1 = None

        if delay_timedelta_cfg_name in cfg:
            _t2 = self.now() + kl.get_interval_timedelta(cfg[delay_timedelta_cfg_name])
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
        #sl_t = kl.get_next_open_time(self.kline_interval, self.now())
        sl_t = self.now() + max(kl.get_next_open_timedelta(kl.KLINE_INTERVAL_1DAY, self.now()), timedelta(hours=4))
        if "base_value" in sl_cfg and sl_cfg["base_value"] > 0 and limit_value * sl_cfg["base_value"] + position_info["floating_profit"] <= 0:
            sl_bills.append(bl.create_bill(position_info["direction"], bl.CLOSE_POSITION, 0, "stop loss", "亏损金额超过额度的{:8.2%}".format(sl_cfg["base_value"]), sl_t))

        # 风控第二条：当前价格低于持仓均价的90%，即刻清仓
        pst_price = get_cost_price(position_info)
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

    def handle_order(self, symbol, position_info, cur_price, check_bills, extra_info=''):
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
        self.send_order(symbol, position_info, cur_price, ds_bill["direction"], ds_bill["action"], ds_bill["pst_rate"], ds_bill["stop_loss_price"], rmk + extra_info)

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

        limit_rate = limit_price_rate["default"]
        if direction == bl.DIRECTION_LONG:
            rate = 1 - limit_rate
        else:
            rate = 1 + limit_rate

        target_coin, base_coin = xq.get_symbol_coins(symbol)

        if action == bl.OPEN_POSITION:
            # 开仓

            if pst_is_lock(position_info):
                # 需要解锁动作
                if True: # 同一账户
                    # 实际持仓已经为空，需发起1笔委托来新增持仓
                    action = bl.UNLOCK_POSITION
                    target_amount = position_info["lock_amount"]

                else:    # 不同账户
                    # 暂不实现
                    return
            else:
                if "pst_rate" in position_info and position_info["pst_rate"] >= pst_rate:
                    return

                if position_info[POSITON_AMOUNT_KEY] == 0:
                    pst_cost = 0
                else:
                    pst_cost = abs(position_info["value"]) + position_info["commission"]
                base_amount = limit_value * pst_rate - pst_cost
                if base_amount <= 0:
                    return

                if direction == bl.DIRECTION_LONG:
                    # 做多开仓
                    '''
                    base_balance = self.get_balances(base_coin)
                    self.log_info("base   balance:  %s" % base_balance)
                    base_amount = min(xq.get_balance_free(base_balance), base_amount)
                    '''
                    self.log_info("base_amount: %g" % base_amount)
                    if base_amount <= 0:  #
                        return
                    target_amount = base_amount / (cur_price * (1 + self.config["commission_rate"]))
                    rate = 1 + limit_price_rate["open"]
                else:
                    # 做空开仓
                    '''
                    target_balance = self.get_balances(target_coin)
                    self.log_info("target balance:  %s" % target_balance)
                    # target_amount = min(xq.get_balance_free(target_balance), base_amount / cur_price)
                    '''
                    target_amount = base_amount / cur_price
                    self.log_info("target_amount: %g" % target_amount)
                    if target_amount <= 0:  #
                        return
                    rate = 1 - limit_price_rate["open"]

        elif action == bl.CLOSE_POSITION:
            # 平仓
            if pst_is_lock(position_info):
                # 需要解锁和平仓2个动作
                if True: # 同一账户
                    # 实际持仓已经为空，不需发起委托，但本次持仓结束
                    self.set_pst_lock_to_close(symbol, rmk)
                    return
                else:    # 不同账户
                    # 需要发起2笔委托，暂不实现
                    return
            else:
                if (not "pst_rate" in position_info) or position_info["pst_rate"] <= pst_rate:
                    return
                target_amount = abs(position_info["amount"]) * (position_info["pst_rate"] - pst_rate) / position_info["pst_rate"]
                if direction == bl.DIRECTION_LONG:
                    # 做多平仓
                    rate = 1 - limit_price_rate["close"]
                else:
                    # 做空平仓
                    rate = 1 + limit_price_rate["close"]

        elif action == bl.LOCK_POSITION:
            # 锁仓
            if pst_is_lock(position_info): # 已经锁仓
                return

            if (not "pst_rate" in position_info) or position_info["pst_rate"] <= 0: # 没有仓位
                return

            target_amount = position_info[POSITON_AMOUNT_KEY]

        elif action == bl.UNLOCK_POSITION:
            # 解锁仓
            if not pst_is_lock(position_info): # 没有锁仓
                return
            target_amount = position_info[LOCK_POSITON_AMOUNT_KEY]
        else:
            return

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
        if order["direction"] not in bl.directions:
            self.log_error("错误的委托方向")
            return False
        if order["action"] not in bl.actions:
            self.log_error("错误的委托动作")
            return False
        return True

    '''
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
    '''


    def handle(self, symbol, strategy, price, create_time, info):
        position_info = self.get_position(symbol, price)
        check_bills = strategy.check_bill(symbol, position_info)
        self.handle_order(symbol, position_info, price, check_bills, info)

    def analyze_orders(self, orders):
        if len(orders) == 0:
            return
        analyze_profit_by_orders(orders, self.config["commission_rate"], self.value, self.config["mode"])


    def display(self, symbol, orders, end_price, end_time, print_switch_hl=True, display_rmk=False):
        #print("oders len:  %s" % len(orders))
        #pprint(orders)
        print_switch_deal = False
        print_switch_commission = False
        print_switch_profit = False

        title = " id"
        title += "         profit_rate"
        title += "          create_time       price"
        title += "               pst_rate"

        if print_switch_deal:
            title += "  deal_amount  deal_value"
        if print_switch_commission:
            title += "  total_commission"
        if print_switch_profit:
            title += "        profit(total)"
        title += "     rmk"
        print(title)

        cycle_id = 0
        for index ,order in enumerate(orders):
            order["cycle_id"] = cycle_id
            pst = order[POSITON_KEY]

            if pst[POSITON_AMOUNT_KEY] == 0: # position end
                cycle_id += 1

            pst_profit = pst[POSITON_PROFIT_KEY]
            total_profit = pst[TOTAL_PROFIX_KEY]
            pst_profit_rate = pst[POSITON_PROFIT_RATE_KEY]
            total_profit_rate = pst[TOTAL_PROFIX_RATE_KEY]
            deal_price = order["deal_value"]/order["deal_amount"]

            info = "%3d" % (index)
            info += "  {:8.2%}({:8.2%})".format(pst_profit_rate, total_profit_rate)
            info += "  %s  %10g" % (
                    datetime.fromtimestamp(order["create_time"]),
                    order["deal_value"]/order["deal_amount"],
                )

            info += "  %s,%6s" % (
                    order["direction"],
                    order["action"],
                )
            info += "  {:3.2f}".format(order["pst_rate"])
            if pst_is_lock(pst):
                info += "(-{:3.2f})".format(order["pst_rate"])
            else:
                info += " "*7

            if print_switch_deal:
                info += "  %11g  %10g" % (
                        order["deal_amount"],
                        order["deal_value"],
                    )
            if print_switch_commission:
                info += "  %16g" % (
                        pst[TOTAL_COMMISSION_KEY],
                    )
            if print_switch_profit:
                info += "  {:8.2f}({:9.2f})".format(
                        pst_profit,
                        total_profit,
                    )
            if display_rmk:
                rmk = order["rmk"]
            else:
                rmk = order["rmk"].split(':')[0]
            rmk_start_len = len(info)
            info += "  %s" % (rmk)

            if print_switch_hl and "high" in order:
                total_commission_rate = 0 # 2 * self.config["commission_rate"]
                pst_first_order = order
                if order["direction"] == bl.DIRECTION_LONG:
                    high_profit_rate = order["high"] / deal_price - 1 - total_commission_rate
                else:
                    high_profit_rate = 1 - order["high"] / deal_price - total_commission_rate

                info += "\n%s" % (" "*rmk_start_len)
                info += "  ({:8.2%}".format(high_profit_rate)
                info += "  %10g, %s)" % (order["high"], datetime.fromtimestamp(order["high_time"]))

                pst_first_deal_price = pst_first_order["deal_value"]/pst_first_order["deal_amount"]
                if order["direction"] == bl.DIRECTION_LONG:
                    low_profit_rate = pst_first_order["low"] / pst_first_deal_price - 1 - total_commission_rate
                else:
                    low_profit_rate = 1 - pre_order["low"] / pst_first_deal_price - total_commission_rate
                info += "\n%s" % (" "*rmk_start_len)
                info += "  ({:8.2%}".format(low_profit_rate)
                info += "  %10g, %s)" % (pst_first_order["low"], datetime.fromtimestamp(pst_first_order["low_time"]))

            pre_order = order
            print(info)

        if not orders:
            return

        if order[ORDER_ACTION_KEY] in [bl.OPEN_POSITION, bl.UNLOCK_POSITION]:
            pst = get_pst_by_orders(orders, self.config["commission_rate"])
            floating_profit, total_profit, floating_profit_rate, total_profit_rate = get_floating_profit(pst, self.value, self.config["mode"], end_price)
            print("  {}  {:8.2%}({:8.2%})  {}      {}".format("*", floating_profit_rate, total_profit_rate, end_time, end_price))

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


    def analyze(self, symbol, orders, print_switch_hl=True, display_rmk=False):
        if len(orders) == 0:
            return

        self.analyze_orders(orders)
        latest_price, latest_time = self.md.get_latest_pirce(symbol)
        self.display(symbol, orders, latest_price, latest_time, print_switch_hl, display_rmk)


    def get_pst_by_orders(self, orders):
        commission_rate = self.config["commission_rate"]
        return get_pst_by_orders(orders, commission_rate)


    def get_history(self, pst_info):
        history_profit         = pst_info[HISTORY_PROFIT_KEY]
        history_profit_rate    = history_profit / self.value
        history_commission     = pst_info[HISTORY_COMMISSION_KEY]
        return history_profit, history_profit_rate, history_commission


    def view_history(self, symbol, orders, pst_info):
        print("%s ~ %s    init value: %s" % (
            datetime.fromtimestamp(orders[0]["create_time"]).strftime('%Y-%m-%d'),
            datetime.fromtimestamp(orders[-1]["create_time"]).strftime('%Y-%m-%d'),
            self.value)
        )

        history_profit, history_profit_rate, history_commission = self.get_history(pst_info)
        print("history:  profit = %.2f(%.2f%%)    commission = %.2f" % (history_profit, history_profit_rate*100, history_commission))
        return pst_info


    def search_calc(self, symbol, orders):
        if len(orders) <= 0:
            return 0, 0, 0, 0

        orders_df = pd.DataFrame(orders)
        profit_df, profit_rate_df = self.calc_profit(orders_df)

        win_count = len(profit_rate_df[profit_rate_df > 0])
        loss_count = len(profit_rate_df[profit_rate_df < 0])

        total_profit_rate = profit_df.sum() / self.value
        sum_profit_rate = profit_rate_df.sum()
        return round(total_profit_rate, 4), round(sum_profit_rate, 4), win_count, loss_count


    def calc_profit(self, orders_df):
        pst_df = pd.DataFrame(orders_df[POSITON_KEY].tolist())
        #pprint(pst_df)
        pst_df = pst_df[(pst_df[POSITON_AMOUNT_KEY]==0)]
        #print(pst_df)
        profit_df = pst_df[POSITON_VALUE_KEY] - pst_df[POSITON_COMMISSION_KEY]
        #print(profit_df)

        if self.config["mode"] == 1:
            profit_rate_df = profit_df / (self.value + pst_df[HISTORY_PROFIT_KEY] - profit_df)
        else:
            profit_rate_df = profit_df / (self.value)
        return profit_df, profit_rate_df


    def stat(self, signal_id, orders_df):
        print("\n signal: " + signal_id)
        profit_df, profit_rate_df = self.calc_profit(orders_df)

        w_profit_rates    = profit_rate_df[profit_rate_df > 0]
        l_profit_rates   = profit_rate_df[profit_rate_df < 0]

        win_count = len(w_profit_rates)
        fail_count = len(l_profit_rates)
        if win_count > 0 or fail_count > 0:
            win_rate = win_count / (win_count + fail_count)
        else:
            win_rate = 0
        print("win count: %g, loss count: %g, win rate: %4.2f%%" % (win_count, fail_count, round(win_rate*100, 2)))

        print("profit rate(total: %6.2f%%, max: %6.2f%%, min: %6.2f%%, average: %6.2f%%)" % (round(w_profit_rates.sum()*100, 2), round(w_profit_rates.max()*100, 2), round(w_profit_rates.min()*100, 2), round(w_profit_rates.mean()*100, 2)))
        print("loss   rate(total: %6.2f%%, max: %6.2f%%, min: %6.2f%%, average: %6.2f%%)" % (round(l_profit_rates.sum()*100, 2), round(l_profit_rates.min()*100, 2), round(l_profit_rates.max()*100, 2), round(l_profit_rates.mean()*100, 2)))

        if win_count == 0:
            kelly = 0
        elif fail_count > 0:
            kelly = win_rate - (1-win_rate)/(w_profit_rates.mean()/abs(l_profit_rates.mean()))
        else:
            kelly = win_rate
        print("Kelly Criterion: %.2f%%" % round(kelly*100, 2))


