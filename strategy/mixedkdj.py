#!/usr/bin/python
"""mixed kdj strategy"""
import logging
import pandas as pd
import common.xquant as xq
import utils.indicator as ic
import utils.tools as ts
from strategy.strategy import Strategy


class MixedKDJStrategy(Strategy):
    """docstring for KDJ"""

    def __init__(self, strategy_config, engine):
        super().__init__(strategy_config, engine)

        self.gold_price = 0
        self.gold_timestamp = None
        self.die_price = 0
        self.die_timestamp = None

    def set_gold_fork(self):
        """ kdj指标，金叉 """
        if self.gold_price <= 0:
            self.gold_price = self.cur_price
            self.gold_timestamp = self.engine.now()

    def set_die_fork(self):
        """ kdj指标，死叉 """
        if self.die_price <= 0:
            self.die_price = self.cur_price
            self.die_timestamp = self.engine.now()

    def check(self, symbol):
        """ kdj指标，金叉全买入，下降趋势部分卖出，死叉全卖出 """
        klines = self.engine.get_klines_1day(symbol, 300)
        self.cur_price = pd.to_numeric(klines["close"].values[-1])

        ic.calc_kdj(klines)
        cur_k = klines["kdj_k"].values[-1]
        cur_d = klines["kdj_d"].values[-1]
        cur_j = klines["kdj_j"].values[-1]
        logging.info(" current kdj  J(%f), K(%f), D(%f)", cur_j, cur_k, cur_d)

        y_k = klines["kdj_k"].values[-2]
        y_d = klines["kdj_d"].values[-2]
        y_j = klines["kdj_j"].values[-2]
        logging.info("yestoday kdj  J(%f), K(%f), D(%f)", y_j, y_k, y_d)

        check_signals = []
        offset = 1
        if cur_j - offset > cur_k > cur_d + offset:  # 开仓
            self.set_gold_fork()

            if cur_j < y_j:
                # 下降趋势
                if cur_k < y_k:
                    # j、k 同时下降，最多保留半仓
                    check_signals.append(
                        xq.create_signal(xq.SIDE_SELL, 0.5, "减仓：j、k 同时下降")
                    )

                else:
                    # j 下落，最多保留8成仓位
                    check_signals.append(xq.create_signal(xq.SIDE_SELL, 0.8, "减仓：j 下落"))
            else:
                # 满仓买入
                check_signals.append(
                    xq.create_signal(
                        xq.SIDE_BUY, 1, "开仓：j-%g > k > d+%g" % (offset, offset)
                    )
                )

        elif cur_j + offset < cur_k < cur_d - offset:  # 平仓
            self.set_die_fork()

            # 清仓卖出
            check_signals.append(
                xq.create_signal(xq.SIDE_SELL, 0, "平仓：j+%g < k < d-%g" % (offset, offset))
            )

        else:
            pass

        logging.info("gold price: %f;  time: %s", self.gold_price, self.gold_timestamp)
        logging.info(" die price: %f;  time: %s", self.die_price, self.die_timestamp)

        return check_signals

    def on_tick(self):
        """ tick处理接口 """
        symbol = self.config["symbol"]
        # 之前的挂单全撤掉
        self.engine.cancle_orders(symbol)

        check_signals = self.check(symbol)
        self.engine.handle_order(symbol, self.cur_price, check_signals)
