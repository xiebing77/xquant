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
        if cur_j - offset > cur_k > cur_d + offset:

            if cur_j > y_j + offset and cur_k > y_k + offset:
                # 上升趋势，满仓买入
                check_signals.append(
                    xq.create_signal(
                        xq.SIDE_BUY, 1, "开仓：j-%g > k > d+%g" % (offset, offset)
                    )
                )

            elif cur_j < y_j - offset:
                # 下降趋势
                if cur_k < y_k - offset:
                    # j、k 同时下降，最多保留半仓
                    check_signals.append(
                        xq.create_signal(xq.SIDE_SELL, 0.5, "减仓：j、k 同时下降")
                    )

                elif cur_k > y_k + offset:
                    # j 下落，最多保留8成仓位
                    check_signals.append(xq.create_signal(xq.SIDE_SELL, 0.8, "减仓：j 下落"))
                else:
                    pass
            else:
                pass

        elif cur_j + offset < cur_k < cur_d - offset:

            # 清仓卖出
            check_signals.append(
                xq.create_signal(xq.SIDE_SELL, 0, "平仓：j+%g < k < d-%g" % (offset, offset))
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
