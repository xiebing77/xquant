#!/usr/bin/python
"""simple kdj strategy"""
import logging
import pandas as pd
import common.xquant as xq
import utils.indicator as ic
from strategy.strategy import Strategy


class KDJStrategy(Strategy):
    """ simple KDJ stragegy"""

    def __init__(self, config, debug):
        super().__init__(config, debug)
        self.cur_price = 0

    def check(self, symbol):
        """ kdj指标，金叉全买入，死叉全卖出 """
        k1d = self.engine.get_klines_1day(symbol, 300)

        self.cur_price = pd.to_numeric(k1d["close"].values[-1])

        ic.KDJ(k1d)
        cur_k = k1d["kdj_k"].values[-1]
        cur_d = k1d["kdj_d"].values[-1]
        cur_j = k1d["kdj_j"].values[-1]
        logging.info(" current kdj  J(%f), K(%f), D(%f)", cur_j, cur_k, cur_d)

        desired_side = None
        desired_position_rate = None
        offset = 1
        if (cur_j - offset) > cur_k > (cur_d + offset):  # 开仓
            logging.info("开仓信号: j-%f > k > d+%f", offset, offset)

            # 满仓买入
            desired_side = xq.SIDE_BUY
            desired_position_rate = 1

        elif (cur_j + offset) < cur_k < (cur_d - offset):  # 平仓
            logging.info("平仓信号: j+%f < k < d-%f", offset, offset)

            # 清仓卖出
            desired_side = xq.SIDE_SELL
            desired_position_rate = 0

        else:
            logging.info("木有信号: 不买不卖")

        return desired_side, desired_position_rate

    def on_tick(self):
        """ tick处理接口 """
        symbol = self.config["symbol"]
        # 之前的挂单全撤掉
        self.engine.cancle_orders(symbol)

        desired_side, desired_position_rate = self.check(symbol)
        position_info = self.engine.get_position(symbol, self.cur_price)
        self.handle_order(symbol, desired_side, desired_position_rate, position_info)
