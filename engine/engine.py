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
from setup import mongo_user, mongo_pwd, db_url
import common.xquant as xq
import db.mongodb as md
from exchange.binanceExchange import BinanceExchange
from exchange.okexExchange import OkexExchange


class Engine:
    """引擎"""

    def __init__(self, instance_id, config, db_orders_name=None):
        self.instance_id = instance_id
        self.config = config

        exchange = config["exchange"]
        if exchange == "binance":
            self.kline_column_names = BinanceExchange.get_kline_column_names()
        elif exchange == "okex":
            self.kline_column_names = OkexExchange.get_kline_column_names()

        self.md_db = md.MongoDB(mongo_user, mongo_pwd, exchange, db_url)
        self.td_db = md.MongoDB(mongo_user, mongo_pwd, "xquant", db_url)

        self.value = 100

        if db_orders_name:
            self.db_orders_name = db_orders_name
            self.td_db.ensure_index(db_orders_name, [("instance_id",1),("symbol",1)])

        self.can_open_time = None


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

    def get_kline_column_names(self):
        return self.kline_column_names

    def get_floating_profit(self, direction, amount, value, commission, cur_price):
        if direction == xq.DIRECTION_LONG:
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
            total_profit + cycle_profit

            open_value = self.value
            if self.config["mode"] == 1:
                open_value += info["history_profit"]

            info["floating_profit"] = cycle_profit
            info["floating_profit_rate"] = cycle_profit / open_value

        if orders:
            info["pst_rate"] = orders[-1]["pst_rate"]

        self.log_info(
            "symbol( %s ); current price( %g ); position(%s%s%s  history_profit: %g,  history_commission: %g,  total_profit_rate: %g)" % (
            symbol,
            cur_price,
            "amount: %f,  price: %g, cost price: %g,  value: %g,  commission: %g,  limit: %g,  profit: %g,"
            % (
                info["amount"],
                info["price"],
                info["cost_price"],
                info["value"],
                info["commission"],
                self.value,
                info["floating_profit"],
            )
            if info["amount"]
            else "",
            "  profit rate: %g,"
            % (info["floating_profit_rate"])
            if info["value"]
            else "",
            "  start_time: %s\n," % info["start_time"].strftime("%Y-%m-%d %H:%M:%S")
            if "start_time" in info and info["start_time"]
            else "",
            info["history_profit"],
            info["history_commission"],
            (total_profit / self.value)
            )
        )
        # print(info)
        return info

    def risk_control(self, position_info, cur_price):
        """ 风控 """
        if position_info["amount"] == 0:
            return []

        sl_signals = self.stop_loss(position_info, cur_price)
        tp_signals = self.take_profit(position_info, cur_price)
        return sl_signals + tp_signals

    def stop_loss(self, position_info, cur_price):
        """ 止损 """
        sl_signals = []
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

        if "base_value" in sl_cfg and sl_cfg["base_value"] > 0 and limit_value * sl_cfg["base_value"] + position_info["floating_profit"] <= 0:
            sl_signals.append(xq.create_signal(position_info["direction"], xq.CLOSE_POSITION, 0, "  止损", "亏损金额超过额度的{:8.2%}".format(sl_cfg["base_value"]), ts.get_next_open_timedelta(self.now())))

        # 风控第二条：当前价格低于持仓均价的90%，即刻清仓
        pst_price = position_info["price"]
        if position_info["direction"] == xq.DIRECTION_LONG:
            loss_rate = 1 - (cur_price / pst_price)
        else:
            loss_rate = (cur_price / pst_price) - 1
        if pst_price > 0 and "base_price" in sl_cfg and sl_cfg["base_price"] > 0 and loss_rate  >= sl_cfg["base_price"]:
            sl_signals.append(xq.create_signal(position_info["direction"], xq.CLOSE_POSITION, 0, "  止损", "下跌了持仓均价的{:8.2%}".format(sl_cfg["base_price"]), ts.get_next_open_timedelta(self.now())))

        return sl_signals

    def take_profit(self, position_info, cur_price):
        """ 止盈 """
        tp_signals = []

        if "high" not in position_info:
            return tp_cfg

        tp_cfg = self.config["risk_control"]["take_profit"]

        if position_info["direction"] == xq.DIRECTION_LONG:
            price_offset = position_info["high"] - cur_price
        else:
            price_offset = cur_price - position_info["low"]

        if "base_open" in tp_cfg:
            for bo_band in tp_cfg["base_open"]:
                high_profit_rate = position_info["high"] / position_info["price"] - 1
                cur_profit_rate = cur_price / position_info["price"] - 1
                fall_profit_rate = high_profit_rate - cur_profit_rate
                if high_profit_rate > bo_band[0] and fall_profit_rate >= bo_band[1]:
                    tp_signals.append(xq.create_signal(position_info["direction"], xq.CLOSE_POSITION, 0, "  止盈", "盈利回落(基于持仓价)  fall rate:{:8.2%} ( {:8.2%}, {:8.2%} )".format(fall_profit_rate, bo_band[0], bo_band[1])))
                    break

        if position_info["direction"] == xq.DIRECTION_LONG:
            price_rate = cur_price / position_info["high"]
        else:
            price_rate = position_info["low"] / cur_price
        if "base_high" in tp_cfg and tp_cfg["base_high"] > 0 and price_rate < (1 - tp_cfg["base_high"]):
            tp_signals.append(xq.create_signal(position_info["direction"], xq.CLOSE_POSITION, 0, "  止盈", "盈利回落，基于最高价的{:8.2%}".format(tp_cfg["base_high"])))

        return tp_signals
        """
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
        """

    def handle_order(self, symbol, cur_price, check_signals):
        """ 处理委托 """
        position_info = self.get_position(symbol, cur_price)

        rc_signals = self.risk_control(position_info, cur_price)
        signals = rc_signals + check_signals
        if not signals:
            return
        for signal in signals:
            self.log_info("signal(%r)" % signal["describe"])

        ds_signal = xq.decision_signals(signals)
        self.log_info(
            "decision signal (%s  %s), position rate(%g), describe(%s), can buy after(%s)" % (
            ds_signal["direction"],
            ds_signal["action"],
            ds_signal["pst_rate"],
            ds_signal["describe"],
            ds_signal["can_open_time"]
            )
        )

        if ds_signal["action"] is None:
            return

        if self.can_open_time:
            if self.now() < self.can_open_time:
                # 限定的时间范围内，只能平仓，不能开仓
                if ds_signal["action"] != xq.CLOSE_POSITION:
                    return
            else:
                # 时间范围之外，恢复
                self.can_open_time = None

        if ds_signal["can_open_time"]:
            if not self.can_open_time or (self.can_open_time and self.can_open_time < self.now() + ds_signal["can_open_time"]):
                self.can_open_time = self.now() + ds_signal["can_open_time"]
                self.log_info("can buy time: %s" % self.can_open_time)

        if ds_signal["pst_rate"] > 1 or ds_signal["pst_rate"] < 0:
            self.log_warning("仓位率（%g）超出范围（0 ~ 1）" % ds_signal["pst_rate"])
            return

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

        if ds_signal["action"] == xq.OPEN_POSITION:
            # 开仓
            if "pst_rate" in position_info and position_info["pst_rate"] >= ds_signal["pst_rate"]:
                return

            pst_cost = abs(position_info["value"]) + position_info["commission"]
            base_amount = limit_value * ds_signal["pst_rate"] - pst_cost
            if base_amount <= 0:
                return

            if ds_signal["direction"] == xq.DIRECTION_LONG:
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
                target_amount = min(xq.get_balance_free(target_balance), base_amount / cur_price)
                self.log_info("target_amount: %g" % target_amount)
                if target_amount <= 0:  #
                    return
                rate = 1 - limit_price_rate["open"]
        else:
            # 平仓
            if (not "pst_rate" in position_info) or position_info["pst_rate"] <= ds_signal["pst_rate"]:
                return

            target_amount = abs(position_info["amount"]) * (position_info["pst_rate"] - ds_signal["pst_rate"]) / position_info["pst_rate"]

            if ds_signal["direction"] == xq.DIRECTION_LONG:
                # 做多平仓
                rate = 1 - limit_price_rate["close"]
            else:
                # 做空平仓
                rate = 1 + limit_price_rate["close"]

        target_amount = ts.reserve_float(target_amount, self.config["digits"][target_coin])
        self.log_info("%s %s target amount: %g" % (ds_signal["direction"], ds_signal["action"], target_amount))
        if target_amount <= 0:
            return
        limit_price = ts.reserve_float(cur_price * rate, self.config["digits"][base_coin])
        order_rmk = ds_signal["describe"] + ":  " + ds_signal["rmk"]
        order_id = self.send_order_limit(
            ds_signal["direction"],
            ds_signal["action"],
            symbol,
            ds_signal["pst_rate"],
            cur_price,
            limit_price,
            target_amount,
            "%s, timedelta: %s, can buy after: %s" % (order_rmk, ds_signal["can_open_time"], self.can_open_time) if (ds_signal["can_open_time"] or self.can_open_time) else "%s" % (order_rmk),
        )
        self.log_info(
            "current price: %g;  rate: %g;  order_id: %s" % (cur_price, rate, order_id)
        )

    def check_order(symbol, order):
        if order["direction"] != xq.DIRECTION_LONG and order["direction"] != xq.DIRECTION_SHORT:
            self.log_error("错误的委托方向")
            return False
        if order["action"] != xq.OPEN_POSITION and order["action"] != xq.CLOSE_POSITION:
            self.log_error("错误的委托动作")
            return False
        return True

    def get_order_value(self, order):
        if (order["action"] == xq.OPEN_POSITION and order["direction"] == xq.DIRECTION_LONG) or (order["action"] == xq.CLOSE_POSITION and order["direction"] == xq.DIRECTION_SHORT):
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

            if order["action"] == xq.OPEN_POSITION:
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
            pst_info["cost_price"] = (abs(cycle_value) + cycle_commission) / cycle_amount

            pst_info["direction"] = cycle_first_order["direction"]
            pst_info["start_time"] = datetime.fromtimestamp(cycle_first_order["create_time"])
            if "high" in order:
                pst_info["high"] = cycle_first_order["high"]
                pst_info["low"] = cycle_first_order["low"]

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

            if order["action"] == xq.OPEN_POSITION:
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

        title = "  id"
        title += "  profit_rate(total)"
        title += "          create_time  direction  action      price  pst_rate"

        if print_switch_hl:
            title += "  (                                         )"

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

            info = "%4d" % (index)
            info += "  {:8.2%}({:8.2%})".format(
                order["floating_profit_rate"], order["total_profit_rate"]
            )
            info += "  %s  %9s  %5s  %10g" % (
                    datetime.fromtimestamp(order["create_time"]),
                    order["direction"],
                    order["action"],
                    order["deal_value"]/order["deal_amount"],
                )
            info += "  {:8.2f}".format(order["pst_rate"])

            if print_switch_hl:
                total_commission_rate = 2 * self.config["commission_rate"]
                if "high" in order:
                    deal_price = order["deal_value"]/order["deal_amount"]
                    if order["direction"] == xq.DIRECTION_LONG:
                        tmp_profit_rate = order["high"] / deal_price - 1 - total_commission_rate
                    else:
                        tmp_profit_rate = 1 - order["high"] / deal_price - total_commission_rate

                    info += "  ({:8.2%}".format(tmp_profit_rate)
                    info += "  %10g, %s)" % (order["high"], datetime.fromtimestamp(order["high_time"]))
                else:
                    pre_deal_price = pre_order["deal_value"]/pre_order["deal_amount"]
                    if order["direction"] == xq.DIRECTION_LONG:
                        tmp_profit_rate = pre_order["low"] / pre_deal_price - 1 - total_commission_rate
                    else:
                        tmp_profit_rate = 1 - pre_order["low"] / pre_deal_price - total_commission_rate
                    info += "  ({:8.2%}".format(tmp_profit_rate)
                    info += "  %10g, %s)" % (pre_order["low"], datetime.fromtimestamp(pre_order["low_time"]))

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

        for signal_id in orders_df["signal_id"].drop_duplicates().values:
            #print(signal_id)

            cycle_ids = orders_df[(orders_df["signal_id"]==signal_id)]["cycle_id"]
            #print(cycle_ids)

            self.stat(signal_id, orders_df[(orders_df["cycle_id"].isin(cycle_ids))] )


    def calc(self, symbol, orders):
        if len(orders) <= 0:
            return 0, 0, 0, 0
        orders_df = pd.DataFrame(self.calc_order(symbol, orders))
        close_df = orders_df[(orders_df["action"]==xq.CLOSE_POSITION)]

        win_df = close_df[(close_df["floating_profit_rate"] > 0)]
        loss_df =close_df[(close_df["floating_profit_rate"] < 0)]
        win_count = len(win_df)
        loss_count = len(loss_df)

        total_profit_rate = close_df["floating_profit"].sum() / self.value
        sum_profit_rate = close_df["floating_profit_rate"].sum()
        return round(total_profit_rate, 4), round(sum_profit_rate, 4), win_count, loss_count


    def stat(self, signal_id, orders_df):
        print("\n signal: " + signal_id)
        win_df = orders_df[(orders_df["action"]==xq.CLOSE_POSITION) & (orders_df["floating_profit_rate"] > 0)]
        loss_df =orders_df[(orders_df["action"]==xq.CLOSE_POSITION) & (orders_df["floating_profit_rate"] < 0)]

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


    def display(self, symbol, orders, klines):

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
        fig, axes = plt.subplots(5,1, sharex=True)
        fig.subplots_adjust(left=0.04, bottom=0.04, right=1, top=1, wspace=0, hspace=0)

        trade_times = [order["trade_time"] for order in orders]

        quotes = []
        for k in klines:
            d = datetime.fromtimestamp(k[0]/1000)
            quote = (dts.date2num(d), float(k[1]), float(k[4]), float(k[2]), float(k[3]))
            quotes.append(quote)

        mpf.candlestick_ochl(axes[0], quotes, width=0.2, colorup='g', colordown='r')
        axes[0].set_ylabel('price')
        axes[0].grid(True)
        axes[0].autoscale_view()
        axes[0].xaxis_date()
        axes[0].plot(trade_times, [(order["deal_value"] / order["deal_amount"]) for order in orders], "o--")

        klines_df = pd.DataFrame(klines, columns=self.kline_column_names)
        open_times = [datetime.fromtimestamp((open_time/1000)) for open_time in klines_df["open_time"]]
        klines_df["close"] = pd.to_numeric(klines_df["close"])
        base_close = klines_df["close"].values[0]

        klines_df["ATR"] = talib.ATR(klines_df["high"], klines_df["low"], klines_df["close"], timeperiod=14)
        klines_df["NATR"] = talib.NATR(klines_df["high"], klines_df["low"], klines_df["close"], timeperiod=14)
        klines_df["TRANGE"] = talib.TRANGE(klines_df["high"], klines_df["low"], klines_df["close"])

        axes[0].plot(open_times, klines_df["ATR"]*10, "y:", label="ATR")

        axes[1].set_ylabel('volatility')
        axes[1].grid(True)
        axes[1].plot(open_times, klines_df["ATR"], "y:", label="ATR")
        axes[1].plot(open_times, klines_df["NATR"], "k--", label="NATR")
        axes[1].plot(open_times, klines_df["TRANGE"], "c--", label="TRANGE")

        ks, ds, js = ic.pd_kdj(klines_df)
        axes[2].set_ylabel('kdj')
        axes[2].grid(True)
        axes[2].plot(open_times, ks, "b", label="k")
        axes[2].plot(open_times, ds, "y", label="d")
        axes[2].plot(open_times, js, "m", label="j")

        axes[-2].set_ylabel('total profit rate')
        axes[-2].grid(True)
        axes[-2].plot(trade_times, [round(100*order["total_profit_rate"], 2) for order in orders], "go--")
        axes[-2].plot(open_times, [round(100*((close/base_close)-1), 2) for close in klines_df["close"]], "r--")

        axes[-1].set_ylabel('rate')
        axes[-1].grid(True)
        #axes[-1].set_label(["position rate", "profit rate"])
        axes[-1].plot(trade_times ,[round(100*order["pst_rate"], 2) for order in orders], "k-", drawstyle="steps-post", label="position")
        axes[-1].plot(trade_times ,[round(100*order["floating_profit_rate"], 2) for order in orders], "g--", drawstyle="steps", label="profit")
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

