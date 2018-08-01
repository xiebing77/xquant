#!/usr/bin/python
import time
import datetime
import numpy as np
import pandas as pd
import talib
import common.xquant as xquant
from utils.indicator import *
import utils.utils as utils
import logging
from strategy.strategy import Strategy


class MixedKDJStrategy(Strategy):
    """docstring for KDJ"""
    def __init__(self, config, debug):
        super().__init__(config, debug)
  
        self.gold_price = 0
        self.die_price = 0

    def set_gold_fork(self):
        if self.gold_price <= 0:
            self.gold_price = self.cur_price
            self.gold_timestamp = datetime.datetime.now()

        logging.info('gold price: %f;  time: %s', self.gold_price, self.gold_timestamp)


    def set_die_fork(self):
        if self.die_price <= 0:
            self.die_price = self.cur_price
            self.die_timestamp = datetime.datetime.now()

        logging.info('die price: %f;  time: %s', self.die_price, self.die_timestamp)

    def check(self, df, position_info):
        KDJ(df)
        cur_k = df['kdj_k'].values[-1]
        cur_d = df['kdj_d'].values[-1]
        cur_j = df['kdj_j'].values[-1]
        logging.info('current kdj  J(%f), K(%f), D(%f)', cur_j, cur_k, cur_d)

        y_k = df['kdj_k'].values[-2]
        y_d = df['kdj_d'].values[-2]
        y_j = df['kdj_j'].values[-2]
        logging.info('yestoday kdj  J(%f), K(%f), D(%f)', y_j, y_k, y_d)

        desired_side = None
        desired_position_rate = None
        if cur_j-1 > cur_k and cur_k > cur_d+1: # 开仓
            logging.info('开仓信号: j-1 > k > d+1')
            self.set_gold_fork()

            if cur_j < y_j:
                # 下降趋势
                if cur_k < y_k:
                    # j、k 同时下降，最多保留半仓
                    desired_side = xquant.SIDE_SELL
                    desired_position_rate = 0.5
                else:
                    # j 下落，最多保留8成仓位
                    desired_side = xquant.SIDE_SELL
                    desired_position_rate = 0.8
            else:
                # 满仓买入
                desired_side = xquant.SIDE_BUY
                desired_position_rate = 1

        elif cur_j+1 < cur_k and cur_k < cur_d-1 : # 平仓
            logging.info('平仓信号: j+1 < k < d-1')
            self.set_die_fork()

            # 清仓卖出
            desired_side = xquant.SIDE_SELL
            desired_position_rate = 0

        else:
            logging.info('木有信号: 不买不卖')

        # today_fall_rate = self.cacl_today_fall_rate(df)
        period_fall_rate = self.cacl_period_fall_rate(df, position_info["start_time"])
        if period_fall_rate > 0.1:  # 平仓
            # 清仓卖出
            desired_side = xquant.SIDE_SELL
            desired_position_rate = 0
        '''
        elif today_fall_rate > 0.05: # 减仓一半
            pass
        '''
        return desired_side, desired_position_rate


    def OnTick(self):
        symbol = self.config['symbol']
        # 之前的挂单全撤掉
        self.engine.cancle_orders(symbol)

        # 
        df = self.engine.get_klines_1day(symbol, 300)

        self.cur_price = pd.to_numeric(df['close'].values[-1])
        position_info = self.engine.get_position(symbol, self.cur_price)

        desired_side, desired_position_rate = self.check(df, position_info)

        self.handle_order(symbol, desired_side, desired_position_rate, df, position_info)
        return



if __name__ == "__main__":

    s = MixedKDJStrategy(debug=True)
    s.run()
