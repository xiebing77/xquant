#!/usr/bin/python
"""mixed kdj strategy"""
import datetime
import logging
import pandas as pd
import common.xquant as xq
import utils.indicator as ic
import utils.tools as ts
from strategy.strategy import Strategy


class MixedKDJStrategy(Strategy):
    """docstring for KDJ"""

    def __init__(self, config, debug):
        super().__init__(config, debug)

        self.gold_price = 0
        self.gold_timestamp = None
        self.die_price = 0
        self.die_timestamp = None

    def set_gold_fork(self, cur_price):
        """ kdj指标，金叉 """
        if self.gold_price <= 0:
            self.gold_price = cur_price
            self.gold_timestamp = datetime.datetime.now()

        logging.info("gold price: %f;  time: %s", self.gold_price, self.gold_timestamp)

    def set_die_fork(self, cur_price):
        """ kdj指标，死叉 """
        if self.die_price <= 0:
            self.die_price = cur_price
            self.die_timestamp = datetime.datetime.now()

        logging.info("die price: %f;  time: %s", self.die_price, self.die_timestamp)

    def check(self, klines, position_info, cur_price):
        """ kdj指标，金叉全买入，下降趋势部分卖出，死叉全卖出 """
        ic.calc_kdj(klines)
        cur_k = klines["kdj_k"].values[-1]
        cur_d = klines["kdj_d"].values[-1]
        cur_j = klines["kdj_j"].values[-1]
        logging.info(" current kdj  J(%f), K(%f), D(%f)", cur_j, cur_k, cur_d)

        y_k = klines["kdj_k"].values[-2]
        y_d = klines["kdj_d"].values[-2]
        y_j = klines["kdj_j"].values[-2]
        logging.info("yestoday kdj  J(%f), K(%f), D(%f)", y_j, y_k, y_d)

        desired_side = None
        desired_position_rate = None
        if cur_j - 1 > cur_k > cur_d + 1:  # 开仓
            logging.info("开仓信号: j-1 > k > d+1")
            self.set_gold_fork(cur_price)

            if cur_j < y_j:
                # 下降趋势
                if cur_k < y_k:
                    # j、k 同时下降，最多保留半仓
                    desired_side = xq.SIDE_SELL
                    desired_position_rate = 0.5
                else:
                    # j 下落，最多保留8成仓位
                    desired_side = xq.SIDE_SELL
                    desired_position_rate = 0.8
            else:
                # 满仓买入
                desired_side = xq.SIDE_BUY
                desired_position_rate = 1

        elif cur_j + 1 < cur_k < cur_d - 1:  # 平仓
            logging.info("平仓信号: j+1 < k < d-1")
            self.set_die_fork(cur_price)

            # 清仓卖出
            desired_side = xq.SIDE_SELL
            desired_position_rate = 0

        else:
            logging.info("木有信号: 不买不卖")

        if position_info["amount"] > 0:
            # today_fall_rate = self.cacl_today_fall_rate(klines)
            period_fall_rate = ts.cacl_period_fall_rate(
                klines, position_info["start_time"], cur_price
            )
            if period_fall_rate > 0.1:  # 平仓
                # 清仓卖出
                desired_side = xq.SIDE_SELL
                desired_position_rate = 0
            """
            elif today_fall_rate > 0.05: # 减仓一半
                pass
            """
        return desired_side, desired_position_rate

    def on_tick(self):
        """ tick处理接口 """
        symbol = self.config["symbol"]
        # 之前的挂单全撤掉
        self.engine.cancle_orders(symbol)

        #
        klines = self.engine.get_klines_1day(symbol, 300)

        cur_price = pd.to_numeric(klines["close"].values[-1])
        position_info = self.engine.get_position(symbol, cur_price)

        desired_side, desired_position_rate = self.check(
            klines, position_info, cur_price
        )

        self.handle_order(
            symbol, cur_price, desired_side, desired_position_rate, position_info
        )
