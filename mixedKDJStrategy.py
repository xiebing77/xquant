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
    def __init__(self, debug):

        self._arguments = [['-limit', 'base coin limit']]

        super().__init__(debug)

        args = self._args
  
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


    def OnTick(self):
        # 之前的挂单全撤掉
        self.engine.cancle_orders(self.symbol)

        # 计算指标
        df = self.engine.get_klines_1day(self.symbol, 300)
        self.cur_price = pd.to_numeric(df['close'].values[-1])
        logging.info('current price: %f', self.cur_price)

        # 持仓
        position_amount, position_cost, start_time = self.engine.get_position(self.symbol, self.cur_price)
        profit = position_amount * self.cur_price - position_cost
        cost_price = 0
        logging.info('position:  symbol(%s), amount(%f), cost(%f), profit(%f), start_time(%s)' % 
            (self.symbol, position_amount, position_cost, profit, start_time))
        if amount > 0:
            cost_price = position_cost / position_amount
            logging.info('position:  symbol(%s), cost price(%s)' % (self.symbol, cost_price))

        if position_amount > 0:
            today_fall_rate = cacl_today_fall_rate(df)
            period_fall_rate = cacl_period_fall_rate(df, start_time)


        KDJ(df)
        kdj_k_cur = df['kdj_k'].values[-1]
        kdj_d_cur = df['kdj_d'].values[-1]
        kdj_j_cur = df['kdj_j'].values[-1]
        logging.info('current kdj K: %f; D: %f; J: %f', kdj_k_cur, kdj_d_cur, kdj_j_cur)
        if kdj_j_cur-1 > kdj_k_cur and kdj_k_cur > kdj_d_cur+1: # 开仓
            logging.info('开仓信号: j-1 > k > d+1')
            self.set_gold_fork()

            if position_amount > 0: # 持仓
                pass
            else:                   # 空仓
                self.limit_buy(self.symbol, self.limit_base_amount)
                return

        elif kdj_j_cur+1 < kdj_k_cur and kdj_k_cur < kdj_d_cur-1 : # 平仓
            logging.info('平仓信号: j+1 < k < d-1')
            self.set_die_fork()

            self.limit_sell(self.symbol, position_amount)
            return

        else:
            logging.info('木有信号: 不买不卖')
            return


if __name__ == "__main__":

    s = MixedKDJStrategy(debug=True)
    s.run()
