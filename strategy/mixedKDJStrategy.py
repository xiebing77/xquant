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

    def check_kdj(self, df):
        KDJ(df)
        cur_k = df['kdj_k'].values[-1]
        cur_d = df['kdj_d'].values[-1]
        cur_j = df['kdj_j'].values[-1]
        logging.info('current kdj  J(%f), K(%f), D(%f)', cur_j, cur_k, cur_d)

        y_k = df['kdj_k'].values[-2]
        y_d = df['kdj_d'].values[-2]
        y_j = df['kdj_j'].values[-2]
        logging.info('yestoday kdj  J(%f), K(%f), D(%f)', y_j, y_k, y_d)

        if cur_j-1 > cur_k and cur_k > cur_d+1: # 开仓
            logging.info('开仓信号: j-1 > k > d+1')
            self.set_gold_fork()

            if cur_j < y_j:
                if cur_k < y_k:
                    return xquant.SIDE_SELL, 0.5 # j、k同时下降，半仓
                else:
                    return xquant.SIDE_SELL, 0.8 # j下落，8成仓位
            else:
                return xquant.SIDE_BUY, 1    # 满仓买入

        elif cur_j+1 < cur_k and cur_k < cur_d-1 : # 平仓
            logging.info('平仓信号: j+1 < k < d-1')
            self.set_die_fork()

            return xquant.SIDE_SELL, 0 # 清仓卖出

        else:
            logging.info('木有信号: 不买不卖')
            return

    def handle_order(self, symbol, side, desired_position_rate, df):

        # 持仓
        position_amount, position_cost, start_time = self.engine.get_position(symbol, self.cur_price)
        profit = position_amount * self.cur_price - position_cost
        cost_price = 0
        if position_amount > 0:
            cost_price = position_cost / position_amount
        logging.info('position:  symbol(%s), current price(%f), cost price(%s), amount(%f), cost(%f), profit(%f), start_time(%s)' %
            (symbol, self.cur_price, cost_price, position_amount, position_cost, profit, start_time))

        # today_fall_rate = self.cacl_today_fall_rate(df)
        period_fall_rate = self.cacl_period_fall_rate(df, start_time)
        if period_fall_rate > 0.1:  # 平仓
            if position_amount > 0:
                self.limit_sell(symbol, position_amount)
            return
        '''
        elif today_fall_rate > 0.05: # 减仓一半
            pass
        '''

        if desired_position_rate > 1 or desired_position_rate < 0:
            return

        target_coin, base_coin = xquant.get_symbol_coins(symbol)
        limit_base_amount = self.config['limit']
        if side == xquant.SIDE_BUY:
            desired_position_value = limit_base_amount * desired_position_rate
            buy_base_amount = desired_position_value - position_cost
            self.limit_buy(symbol, utils.reserve_float(buy_base_amount),self.config['digits'][base_coin])
        elif side == xquant.SIDE_SELL:
            position_rate = position_cost / limit_base_amount
            desired_position_amount = position_amount * desired_position_rate / position_rate
            sell_target_amount = position_amount - utils.reserve_float(desired_position_amount, self.config['digits'][target_coin])
            self.limit_sell(symbol, sell_target_amount)
        else:
            return


    def OnTick(self):
        symbol = self.config['symbol']
        # 之前的挂单全撤掉
        self.engine.cancle_orders(symbol)

        # 
        df = self.engine.get_klines_1day(symbol, 300)
        self.cur_price = pd.to_numeric(df['close'].values[-1])
        side, desired_position_rate = self.check_kdj(df)
        self.handle_order(symbol, side, desired_position_rate, df)



if __name__ == "__main__":

    s = MixedKDJStrategy(debug=True)
    s.run()
