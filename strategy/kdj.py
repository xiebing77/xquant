#!/usr/bin/python
"""simple kdj strategy"""
import logging
import pandas as pd
import common.xquant as xq
import utils.indicator as ic
from strategy.strategy import Strategy


class KDJStrategy(Strategy):
    """ simple KDJ stragegy"""

    def __init__(self, strategy_config, engine):
        super().__init__(strategy_config, engine)
        self.cur_price = 0

    def check(self, symbol):
        """ kdj指标，金叉全买入，死叉全卖出 """
        klines = self.engine.get_klines_1day(symbol, 300)
        self.cur_price = float(klines[-1][4])

        kdj_arr = ic.py_kdj(klines)
        cur_k = kdj_arr[-1][1]
        cur_d = kdj_arr[-1][2]
        cur_j = kdj_arr[-1][3]

        y_k = kdj_arr[-2][1]
        y_d = kdj_arr[-2][2]
        y_j = kdj_arr[-2][3]

        """
        self.cur_price = pd.to_numeric(k1d["close"].values[-1])
        ic.calc_kdj(k1d)
        cur_k = k1d["kdj_k"].values[-1]
        cur_d = k1d["kdj_d"].values[-1]
        cur_j = k1d["kdj_j"].values[-1]
        """

        logging.info(" current kdj  J(%f), K(%f), D(%f)", cur_j, cur_k, cur_d)

        check_signals = []
        offset = 1
        if (cur_j - offset) > cur_k > (cur_d + offset):  # 开仓
            # 满仓买入
            check_signals.append(
                xq.create_signal(
                    xq.SIDE_BUY, 1, "开仓：j-%g > k > d+%g" % (offset, offset)
                )
            )

        elif (cur_j + offset) < cur_k < (cur_d - offset):  # 平仓
            # 清仓卖出
            check_signals.append(
                xq.create_signal(
                    xq.SIDE_SELL, 0, "平仓：j+%g < k < d-%g" % (offset, offset)
                )
            )

        else:
            pass

        return check_signals

    def on_tick(self):
        """ tick处理接口 """
        symbol = self.config["symbol"]
        # 之前的挂单全撤掉
        self.engine.cancle_orders(symbol)

        check_signals = self.check(symbol)
        self.engine.handle_order(symbol, self.cur_price, check_signals)
