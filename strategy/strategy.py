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

class Strategy(object):
    """docstring for Strategy"""

    def __init__(self, debug=False):
        self.debug_flag = debug
        print('self.debug_flag: ', self.debug_flag)

        parser = argparse.ArgumentParser(description='coin trade')
        parser.add_argument('-symbol', help='symbol')
        parser.add_argument('-digits', help='coins digits')

        parser.add_argument('-e', help='exchange name')
        parser.add_argument('-s', help='tick second')
        parser.add_argument('-r', help='email receiver')
        parser.add_argument('-i', help='instance No')

        for argument in self._arguments:
            parser.add_argument(argument[0], help=argument[1])

        args = parser.parse_args()
        print(args)

        self._args = args

        self.symbol = args.symbol
        self.digits = json.loads(args.digits)
        self.id = self.__class__.__name__ + '_' + self.symbol + '_' + args.i
        self.interval = args.s
        self.limit_base_amount = float(args.limit)

        logfilename = self.id + '_' + datetime.datetime.now().strftime('%Y%m%d') + '.log'
        print(logfilename)
        logging.basicConfig(level=logging.NOTSET, filename=logfilename)

        logging.info('strategy name: %s;  args: %s', self.__class__.__name__, args)

        self.engine = RealEngine(args.e, self.id)

    # 计算当天最高价的回落比例
    def cacl_today_fall_rate(self, df):
        today_high_price = pd.to_numeric(df['high'].values[-1])
        today_fall_rate = (1 - self.cur_price / today_high_price) * 100
        logging.info('today high price:%f;  fall rate: %f%% ;', today_high_price, today_fall_rate)
        return today_fall_rate

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

        period_fall_rate = (1 - self.cur_price / period_high_price) * 100
        #print('start_timestamp: %s, period_high_price: %f, period_fall_rate: %f' % (start_timestamp, period_high_price, period_fall_rate))
        logging.info('period high price: %f, fall rate: %f%%, start time: %s' % (period_high_price, period_fall_rate, start_time))
        return period_fall_rate

    def limit_buy(self, symbol, base_coin_amount):
        target_coin, base_coin = xquant.get_symbol_coins(symbol)
        base_balance = self.engine.get_balances(base_coin)
        logging.info('base   balance:  %s', base_balance)

        free_base_amount = utils.str_to_float(base_balance['free'])
        buy_base_amount = min(free_base_amount, base_coin_amount)
        logging.info('buy_base_amount: %f',buy_base_amount)

        if buy_base_amount <= 0: #
            return

        target_amount_digits = self.digits[target_coin]
        buy_target_amount = utils.reserve_float(buy_base_amount / self.cur_price, target_amount_digits)
        logging.info('buy target coin amount: %f', buy_target_amount)

        base_amount_digits = self.digits[base_coin]
        limit_buy_price = utils.reserve_float(self.cur_price * 1.1, base_amount_digits)
        order_id = self.engine.send_order(xquant.SIDE_BUY, xquant.ORDER_TYPE_LIMIT, symbol, limit_buy_price, buy_target_amount)
        logging.info('current price: %f;  limit buy price: %f;  order_id: %s ',self.cur_price, limit_buy_price, order_id)
        return


    def limit_sell(self, symbol, target_coin_amount):
        if target_coin_amount <= 0:
            return
        logging.info('sell target coin num: %f',target_coin_amount)

        target_coin, base_coin = xquant.get_symbol_coins(symbol)
        base_amount_digits = self.digits[base_coin]
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
            time.sleep(int(self.interval))

		
