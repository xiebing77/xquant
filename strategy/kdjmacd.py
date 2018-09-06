#!/usr/bin/python
"""mixed kdj strategy"""
import logging
from datetime import timedelta,datetime
from collections import namedtuple
import pandas as pd
import common.xquant as xq
import utils.indicator as ic
import utils.tools as ts
from strategy.strategy import Strategy


class KDJMACDStrategy(Strategy):
    """KDJ MACD"""

    def __init__(self, strategy_config, engine):
        super().__init__(strategy_config, engine)

        for index,value in enumerate(self.engine.get_kline_column_names()):
            if value == "close":
                self.closeindex = index
                break


    def check(self, symbol):
        """ kdj指标，金叉全买入，下降趋势部分卖出，死叉全卖出 """
        klines = self.engine.get_klines_1day(symbol, 300)
        self.cur_price = float(klines[-1][4])

        kdj_arr = ic.py_kdj(klines)

        cur_k = kdj_arr[-1][1]
        cur_d = kdj_arr[-1][2]
        cur_j = kdj_arr[-1][3]

        y_k = kdj_arr[-2][1]
        y_d = kdj_arr[-2][2]
        y_j = kdj_arr[-2][3]

        logging.info(" current kdj   J(%f),  K(%f),  D(%f)", cur_j, cur_k, cur_d)
        logging.info("yestoday kdj   J(%f),  K(%f),  D(%f)", y_j, y_k, y_d)

        arr = ic.py_macd(klines, self.closeindex)
        dif = arr[-1][2]
        dea = arr[-1][3]
        logging.info(" current macd   dif(%f),  dea(%f)", dif, dea)

        check_signals = []
        offset = 2
        if cur_j - offset > cur_k > cur_d + offset:

            if cur_j > y_j + offset and cur_k > y_k + offset:
                # 上升趋势，满仓买入
                if dif - dea > 80:
                    check_signals.append(
                        xq.create_signal(
                            xq.SIDE_BUY, 1, "开仓：j-%g > k > d+%g; macd(%g, %g, %g)" % (offset, offset, dif, dea, dif-dea)
                        )
                    )

            elif cur_j < y_j - offset:
                # 下降趋势
                if cur_k < y_k - offset:
                    # j、k 同时下降，最多保留半仓
                    check_signals.append(
                        xq.create_signal(xq.SIDE_SELL, 0.5, "减仓：j、k 同时下降; macd(%g, %g, %g)" % (dif, dea, dif-dea))
                    )

                elif cur_k > y_k + offset:
                    # j 下落，最多保留8成仓位
                    if dif - dea < 0:            
                        check_signals.append(xq.create_signal(xq.SIDE_SELL, 0.8, "减仓：j 下落; macd(%g, %g, %g)" % (dif, dea, dif-dea)))
                    #pass
                else:
                    pass
            else:
                pass

        elif cur_j + offset < cur_k < cur_d - offset:

            # 清仓卖出
            check_signals.append(
                xq.create_signal(xq.SIDE_SELL, 0, "平仓：j+%g < k < d-%g; macd(%g, %g, %g)" % (offset, offset, dif, dea, dif-dea))
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
