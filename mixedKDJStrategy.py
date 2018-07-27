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

        super().__init__()

        args = self._args
  
        self.gold_price = 0
        self.die_price = 0

    def set_gold_fork(self, cur_price):
        if self.gold_price <= 0:
            self.gold_price = cur_price
            self.gold_timestamp = datetime.datetime.now()

        logging.info('gold price: %f;  time: %s', self.gold_price, self.gold_timestamp)


    def set_die_fork(self, cur_price):
        if self.die_price <= 0:
            self.die_price = cur_price
            self.die_timestamp = datetime.datetime.now()

        logging.info('die price: %f;  time: %s', self.die_price, self.die_timestamp)


    def OnTick(self):
        # 之前的挂单全撤掉
        self.engine.cancle_orders(self.symbol)

        # 计算指标
        df = self.engine.get_klines_1day(self.symbol, 300)
        KDJ(df)
        kdj_k_cur = df['kdj_k'].values[-1]
        kdj_d_cur = df['kdj_d'].values[-1]
        kdj_j_cur = df['kdj_j'].values[-1]
        cur_price = df['close'].values[-1]
        cur_price = utils.str_to_float(cur_price, self.base_amount_digits)
        logging.info('current price: %f;  kdj_k: %f; kdj_d: %f; kdj: %f', cur_price, kdj_k_cur, kdj_d_cur, kdj_j_cur)

        # 持仓
        position_amount, profit = self.engine.get_position(self.symbol, cur_price)
        logging.info('symbol: %s, position_amount: %f, profit: %f' % (self.symbol, position_amount, profit))

        if kdj_j_cur-1 > kdj_k_cur and kdj_k_cur > kdj_d_cur+1: # 开仓
            logging.info('开仓信号: j-1 > k > d+1')
            self.set_gold_fork(cur_price)

            if position_amount > 0: # 持仓
                pass
            else:                   # 空仓
                target_coin, base_coin = xquant.get_symbol_coins(self.symbol)
                print('target_coin: %s, base_coin: %s' % (target_coin, base_coin))
                target_balance, base_balance = self.engine.get_balances(target_coin, base_coin)
                logging.info('target balance:  %f', target_balance)
                logging.info('base   balance:  %f', base_balance)
                self.limit_buy(utils.str_to_float(base_balance['free'], self.base_amount_digits), cur_price)

        elif kdj_j_cur+1 < kdj_k_cur and kdj_k_cur < kdj_d_cur-1 : # 平仓
            logging.info('平仓信号: j+1 < k < d-1')
            self.set_die_fork(cur_price)

            self.limit_sell(position_amount, cur_price)

        else:
            logging.info('木有信号: 不买不卖')


if __name__ == "__main__":

    s = MixedKDJStrategy(debug=True)
    s.run()
