#!/usr/bin/python
"""运行环境引擎"""
import matplotlib.pyplot as plt
import matplotlib.dates as dts
from matplotlib import gridspec
import mpl_finance as mpf
import pandas as pd
import talib
from datetime import datetime,timedelta
import logging
import utils.tools as ts
import utils.indicator as ic
from setup import mongo_user, mongo_pwd, db_name, db_url
import common.xquant as xq
import db.mongodb as md
from exchange.binanceExchange import BinanceExchange
from exchange.okexExchange import OkexExchange


class Engine:
    """引擎"""

    def __init__(self, instance_id, config, db_orders_name=None):
        self.instance_id = instance_id
        self.config = config
        self._db = md.MongoDB(mongo_user, mongo_pwd, db_name, db_url)

        if db_orders_name:
            self.db_orders_name = db_orders_name
            self._db.ensure_index(db_orders_name, [("instance_id",1),("symbol",1)])

        self.can_buy_time = None

        exchange = config["exchange"]
        if exchange == "binance":
            self.kline_column_names = BinanceExchange.get_kline_column_names()
        elif exchange == "okex":
            self.kline_column_names = OkexExchange.get_kline_column_names()

    def get_kline_column_names(self):
        return self.kline_column_names

    def _get_position(self, symbol, orders, cur_price):
        info = {
            "amount": 0,  # 数量
            "price": 0,  # 平均价格，不包含佣金
            "cost_price": 0,  # 分摊佣金后的成本价
            "value": 0,  # 金额
            "commission": 0,  # 佣金
            "profit": 0,  # 当前利润
            "history_profit": 0,  # 历史利润
            "history_commission": 0,  # 历史佣金
            "start_time": None,  # 本周期第一笔买入时间
            "pst_rate": 0,  # 本次交易完成后要达到的持仓率
        }
        target_coin, base_coin = xq.get_symbol_coins(symbol)

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

            info["amount"] = ts.reserve_float(info["amount"], self.config["digits"][target_coin])

            if info["amount"] == 0:
                info["history_profit"] -= info["value"] + info["commission"]
                info["history_commission"] += info["commission"]
                info["value"] = 0
                info["commission"] = 0
                info["start_time"] = None

        if info["amount"] == 0:
            pass
        elif info["amount"] > 0:
            info["profit"] = (
                cur_price * info["amount"] - info["value"] - info["commission"]
            )
            info["price"] = info["value"] / info["amount"]
            info["cost_price"] = (info["value"] + info["commission"]) / info["amount"]

        else:
            logging.error("持仓数量不可能小于0")

        info["limit_base_amount"] = self.config["limit"]["value"]
        if orders:
            info["pst_rate"] = orders[-1]["pst_rate"]

        logging.info(
            "symbol( %s ); current price( %g ); position(%s%s%s  history_profit: %g,  history_commission: %g,  total_profit_rate: %g)",
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
            "  profit rate: %g,"
            % (info["profit"] / (info["value"] + info["commission"]))
            if info["value"]
            else "",
            "  start_time: %s\n," % info["start_time"].strftime("%Y-%m-%d %H:%M:%S")
            if info["start_time"]
            else "",
            info["history_profit"],
            info["history_commission"],
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
            rc_signals.append(xq.create_signal(xq.SIDE_SELL, 0, "风控平仓：亏损金额超过额度的10%", ts.get_next_open_timedelta(self.now())))

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

        signals = rc_signals + check_signals
        if not signals:
            return

        logging.info("signals(%r)", signals)
        dcs_side, dcs_pst_rate, dcs_rmk, dcs_cba = xq.decision_signals2(signals)
        logging.info(
            "decision signal side(%s), position rate(%g), rmk(%s), can buy after(%s)",
            dcs_side,
            dcs_pst_rate,
            dcs_rmk,
            dcs_cba,
        )

        if dcs_side is None:
            return

        if self.can_buy_time:
            if self.now() < self.can_buy_time:
                # 时间范围之内，只能卖，不能买
                if dcs_side != xq.SIDE_SELL:
                    return
            else:
                # 时间范围之外，恢复
                self.can_buy_time = None

        if dcs_cba:
            if not self.can_buy_time or (self.can_buy_time and self.can_buy_time < self.now() + dcs_cba):
                self.can_buy_time = self.now() + dcs_cba
                logging.info("can buy time: %s", self.can_buy_time)

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

        target_coin, base_coin = xq.get_symbol_coins(symbol)
        if dcs_side == xq.SIDE_BUY:
            if position_info["pst_rate"] >= dcs_pst_rate:
                return

            buy_base_amount = (
                limit_value * dcs_pst_rate
                - position_info["value"]
                - position_info["commission"]
            )
            if buy_base_amount <= 0:
                return

            base_balance = self.get_balances(base_coin)
            logging.info("base   balance:  %s", base_balance)

            buy_base_amount = min(xq.get_balance_free(base_balance), buy_base_amount)
            logging.info("buy_base_amount: %g", buy_base_amount)
            if buy_base_amount <= 0:  #
                return

            target_amount = ts.reserve_float(
                buy_base_amount / (cur_price * (1 + self.config["commission_rate"])),
                self.config["digits"][target_coin],
            )

            rate = 1.1

        elif dcs_side == xq.SIDE_SELL:
            if position_info["pst_rate"] <= dcs_pst_rate:
                return

            target_amount = ts.reserve_float(
                position_info["amount"]
                * (position_info["pst_rate"] - dcs_pst_rate)
                / position_info["pst_rate"],
                self.config["digits"][target_coin],
            )

            rate = 0.9
        else:
            return

        logging.info("%s target amount: %g" % (dcs_side, target_amount))
        if target_amount <= 0:
            return
        limit_price = ts.reserve_float(cur_price * rate, self.config["digits"][base_coin])
        order_id = self.send_order_limit(
            dcs_side,
            symbol,
            dcs_pst_rate,
            cur_price,
            limit_price,
            target_amount,
            "%s, timedelta: %s, can buy after: %s" % (dcs_rmk, dcs_cba, self.can_buy_time) if (dcs_cba or self.can_buy_time) else "%s" % (dcs_rmk),
        )
        logging.info(
            "current price: %g;  rate: %g;  order_id: %s", cur_price, rate, order_id
        )


    def analyze(self, symbol, orders):

        i = 1
        amount = 0
        buy_value = 0
        sell_value = 0
        buy_commission = 0
        sell_commission = 0

        total_commission = 0
        total_profit = 0
        total_profit_rate = 0

        target_coin, base_coin = xq.get_symbol_coins(symbol)
        print(
            "  id          create_time  side  pst_rate   cur_price  deal_amount  deal_value      amount      profit  profit_rate  total_profit  total_profit_rate  total_commission  rmk"
        )
        for index ,order in enumerate(orders):
            if index == 0:
                order["cycle_id"] = 0
            else:
                pre_order = orders[index-1]
                order["cycle_id"] = pre_order["cycle_id"]
                if order["cycle_id"] != pre_order["side"] and order["side"] == xq.SIDE_BUY:
                    order["cycle_id"] += 1

            cur_price = order["deal_value"] / order["deal_amount"]

            deal_value = order["deal_value"]
            commission = deal_value * self.config["commission_rate"]
            total_commission += commission

            if order["side"] == xq.SIDE_BUY:
                amount += order["deal_amount"]
                buy_value += deal_value
                buy_commission += commission
            else:
                amount -= order["deal_amount"]
                sell_value += deal_value
                sell_commission += commission

            amount = ts.reserve_float(amount, self.config["digits"][target_coin])

            buy_cost = buy_value + buy_commission
            pst_value = cur_price * amount
            profit = pst_value + sell_value - sell_commission - buy_cost
            order["profit_rate"] = profit / buy_cost

            tmp_total_profit = total_profit + profit
            tmp_total_profit_rate = tmp_total_profit / self.config["limit"]["value"]
            order["total_profit_rate"] = round(tmp_total_profit_rate * 100, 2)
            order["trade_time"] = datetime.fromtimestamp(order["create_time"])

            if amount == 0:
                total_profit += profit

                buy_value = 0
                sell_value = 0
                buy_commission = 0
                sell_commission = 0
            elif amount > 0:
                pass
            else:
                pass


            print(
                "%4d  %s  %4s  %8g  %10g  %11g  %10g  %10g  %10g  %10.2f%%  %12g  %16.2f%%  %16g  %s"
                % (
                    i,
                    datetime.fromtimestamp(order["create_time"]),
                    order["side"],
                    order["pst_rate"],
                    cur_price,
                    order["deal_amount"],
                    order["deal_value"],
                    amount,
                    profit,
                    round(order["profit_rate"] * 100, 2),
                    tmp_total_profit,
                    order["total_profit_rate"],
                    total_commission,
                    order["rmk"],
                )
            )
            i += 1

        orders_df = pd.DataFrame(orders)

        orders_df["create_time"] = orders_df["create_time"].map(lambda x: datetime.fromtimestamp(x))
        orders_df["deal_price"] = orders_df["deal_value"] / orders_df["deal_amount"]
        orders_df["commission"] = orders_df["deal_value"] * self.config["commission_rate"]


        orders_df["signal_id"] = orders_df["rmk"].map(lambda x: x.split("：")[0])
        orders_df["signal_rmk"] = orders_df["rmk"].map(lambda x: x.split("：")[1])
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



    def stat(self, signal_id, orders_df):
        print("\n signal: " + signal_id)
        win_df = orders_df[(orders_df["side"]==xq.SIDE_SELL) & (orders_df["profit_rate"] > 0)]
        loss_df =orders_df[(orders_df["side"]==xq.SIDE_SELL) & (orders_df["profit_rate"] < 0)]

        win_count = len(win_df)
        fail_count = len(loss_df)
        win_rate = win_count / (win_count + fail_count)
        print("win count: %g, loss count: %g, win rate: %4.2f%%" % (win_count, fail_count, round(win_rate*100, 2)))

        w_profit_rates = win_df["profit_rate"]
        l_profit_rates = loss_df["profit_rate"]
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

        axes[1].set_ylabel('volatility')
        axes[1].grid(True)
        axes[1].plot(open_times, klines_df["ATR"], "r--", label="ATR")
        axes[1].plot(open_times, klines_df["NATR"], "g--", label="NATR")
        axes[1].plot(open_times, klines_df["TRANGE"], "y--", label="TRANGE")

        ks, ds, js = ic.pd_kdj(klines_df)
        axes[2].set_ylabel('kdj')
        axes[2].grid(True)
        axes[2].plot(open_times, ks, "k", label="k")
        axes[2].plot(open_times, ds, "y", label="d")
        axes[2].plot(open_times, js, "m", label="j")

        axes[-2].set_ylabel('total profit rate')
        axes[-2].grid(True)
        axes[-2].plot(trade_times, [order["total_profit_rate"] for order in orders], "go--")
        axes[-2].plot(open_times, [round(100*((close/base_close)-1), 2) for close in klines_df["close"]], "r--")

        axes[-1].set_ylabel('rate')
        axes[-1].grid(True)
        #axes[-1].set_label(["position rate", "profit rate"])
        axes[-1].plot(trade_times ,[round(100*order["pst_rate"], 2) for order in orders], "k-", drawstyle="steps-post", label="position")
        axes[-1].plot(trade_times ,[round(100*order["profit_rate"], 2) for order in orders], "g--", drawstyle="steps", label="profit")
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

