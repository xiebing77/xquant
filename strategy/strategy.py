#!/usr/bin/python
import time
import datetime
import argparse
import logging
import argparse
from engine.realengine import RealEngine 
import common.xquant as xquant
import utils.utils as utils
import json
import pandas as pd

class Strategy(object):
    """docstring for Strategy"""

    def __init__(self, config, debug=False):
        self.config = config
        self.debug_flag = debug

        self.id = self.__class__.__name__ + '_' + self.config['symbol'] + '_' + self.config['id']

        logfilename = self.id + '_' + datetime.datetime.now().strftime('%Y%m%d') + '.log'
        print(logfilename)
        logging.basicConfig(level=logging.NOTSET, filename=logfilename)

        logging.info('strategy name: %s;  config: %s', self.__class__.__name__, config)

        self.engine = RealEngine(self.config['exchange'], self.id)

    # 计算当天最高价的回落比例
    def cacl_today_fall_rate(self, df):
        today_high_price = pd.to_numeric(df['high'].values[-1])
        today_fall_rate = (1 - self.cur_price / today_high_price)
        logging.info('today  high price(%f);  fall rate(%f)', today_high_price, today_fall_rate)
        return today_fall_percent

    # 计算开仓日期到现在最高价的回落比例
    def cacl_period_fall_rate(self, df, start_time):
        if start_time is None:
            return

        start_timestamp = time.mktime(start_time.timetuple())
        # print('start_timestamp: %s, type:%s' % (start_timestamp, type(start_timestamp)))
        period_df = df[df['open_time'].map(lambda x:int(x)) > start_timestamp*1000]
        # print(df)
        # print(period_df)
        period_high_price = period_df['high'].apply(pd.to_numeric).max()
        # print('start_timestamp: %s, period_high_price: %f' % (start_timestamp, period_high_price))

        period_fall_rate = (1 - self.cur_price / period_high_price)
        #print('start_timestamp: %s, period_high_price: %f, period_fall_rate: %f' % (start_timestamp, period_high_price, period_fall_rate))
        logging.info('period high price(%f), fall rate(%f), start time(%s)' % (period_high_price, period_fall_rate, start_time))
        return period_fall_rate


    def risk_control(self, symbol, df, position_info):
        rc_side = None
        rc_position_rate = 1

        # 风控第一条：亏损金额超过额度的10%，如额度1000，亏损金额超过200即刻清仓
        loss_limit = self.config['limit'] * 0.1
        if loss_limit + position_info['profit'] <= 0:
            rc_side = xquant.SIDE_SELL
            rc_position_rate = min(0, rc_position_rate)
            return

        return rc_side, rc_position_rate


    def handle_order(self, symbol, desired_side, desired_position_rate, df, position_info):
        # 风控
        rc_side, rc_position_rate = self.risk_control(symbol, df, position_info)
        if rc_side == xquant.SIDE_BUY:
            logging.warning('风控方向不能为买')
            return

        if rc_side == xquant.SIDE_SELL:
            if desired_side == xquant.SIDE_SELL:
                desired_position_rate = min(rc_position_rate, desired_position_rate)
            else:
                desired_side = xquant.SIDE_SELL
                desired_position_rate = rc_position_rate

        if desired_position_rate > 1 or desired_position_rate < 0:
            return

        target_coin, base_coin = xquant.get_symbol_coins(symbol)
        limit_base_amount = self.config['limit']
        if desired_side == xquant.SIDE_BUY:
            desired_position_value = limit_base_amount * desired_position_rate
            buy_base_amount = desired_position_value - position_info["cost"]
            self.limit_buy(symbol, utils.reserve_float(buy_base_amount),self.config['digits'][base_coin])
        elif desired_side == xquant.SIDE_SELL:
            position_rate = position_info["cost"] / limit_base_amount
            desired_position_amount = position_info["amount"] * desired_position_rate / position_rate
            sell_target_amount = position_info["amount"] - utils.reserve_float(desired_position_amount, self.config['digits'][target_coin])
            self.limit_sell(symbol, sell_target_amount)
        else:
            return

    def limit_buy(self, symbol, base_coin_amount):
        if base_coin_amount <= 0:
            return

        target_coin, base_coin = xquant.get_symbol_coins(symbol)
        base_balance = self.engine.get_balances(base_coin)
        logging.info('base   balance:  %s', base_balance)

        free_base_amount = utils.str_to_float(base_balance['free'])
        buy_base_amount = min(free_base_amount, base_coin_amount)
        logging.info('buy_base_amount: %f',buy_base_amount)

        if buy_base_amount <= 0: #
            return

        target_amount_digits = self.config['digits'][target_coin]
        buy_target_amount = utils.reserve_float(buy_base_amount / self.cur_price, target_amount_digits)
        logging.info('buy target coin amount: %f', buy_target_amount)

        base_amount_digits = self.config['digits'][base_coin]
        limit_buy_price = utils.reserve_float(self.cur_price * 1.1, base_amount_digits)
        order_id = self.engine.send_order(xquant.SIDE_BUY, xquant.ORDER_TYPE_LIMIT, symbol, limit_buy_price, buy_target_amount)
        logging.info('current price: %f;  limit buy price: %f;  order_id: %s ',self.cur_price, limit_buy_price, order_id)
        return


    def limit_sell(self, symbol, target_coin_amount):
        if target_coin_amount <= 0:
            return
        logging.info('sell target coin num: %f',target_coin_amount)

        target_coin, base_coin = xquant.get_symbol_coins(symbol)
        base_amount_digits = self.config['digits'][base_coin]
        limit_sell_price = utils.reserve_float(self.cur_price * 0.9, base_amount_digits)
        order_id = self.engine.send_order(xquant.SIDE_SELL, xquant.ORDER_TYPE_LIMIT, symbol, limit_sell_price, target_coin_amount)
        logging.info('current price: %f;  limit sell price: %f;  order_id: %s',self.cur_price, limit_sell_price, order_id)


    def run(self):

        while True:
            tickStart = datetime.datetime.now()
            logging.info('%s OnTick start......................................', tickStart)
            if self.debug_flag:
                self.OnTick()
            else:
                try:
                    self.OnTick()
                except Exception as e:
                    logging.critical(e)
            tickEnd = datetime.datetime.now()
            logging.info('%s OnTick end...; tick  cost: %s -----------------------\n\n', tickEnd, tickEnd-tickStart)
            time.sleep(self.config['sec'])

		
