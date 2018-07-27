#!/usr/bin/python
import time
import datetime
import argparse
import logging
import argparse
from engine.realengine import RealEngine 
import common.xquant as xquant
import utils.utils as utils

class Strategy(object):
    """docstring for Strategy"""

    def __init__(self, debug=False):
        self.debug_flag = debug

        parser = argparse.ArgumentParser(description='coin trade')
        parser.add_argument('-b', help='base coin')
        parser.add_argument('-t', help='target coin')
        parser.add_argument('-a', help='target amount digits')
        parser.add_argument('-d', help='base amount digits')
        parser.add_argument('-p', help='price digits')
        parser.add_argument('-e', help='exchange name')
        parser.add_argument('-s', help='tick second')
        parser.add_argument('-r', help='email receiver')
        parser.add_argument('-i', help='instance No')

        for argument in self._arguments:
            parser.add_argument(argument[0], help=argument[1])

        args = parser.parse_args()
        print(args)

        self._args = args

        self.symbol = xquant.creat_symbol(args.t, args.b)
        self.id = self.__class__.__name__ + '_' + self.symbol + '_' + args.i
        self.interval = args.s
        self.base_amount_digits = int(args.p)
        self.target_amount_digits = int(args.a)
        self.limit_base_amount = float(args.limit)

        logfilename = self.id + '_' + datetime.datetime.now().strftime('%Y%m%d') + '.log'
        print(logfilename)
        logging.basicConfig(level=logging.NOTSET, filename=logfilename)

        logging.info('strategy name: %s;  args: %s', self.__class__.__name__, args)

        self.engine = RealEngine(args.e, self.id)

    def limit_buy(self, free_base_amount, cur_price):
        cost_base_amount = min(free_base_amount, self.limit_base_amount)
        logging.info('cost_base_amount: %f',cost_base_amount)

        if cost_base_amount <= 0: #
            return

        buy_target_amount = utils.reserve_float(cost_base_amount / cur_price, self.target_amount_digits)
        logging.info('buy target coin amount: %f', buy_target_amount)
        limit_buy_price = utils.reserve_float(cur_price * 1.1, self.base_amount_digits)
        order_id = self.engine.send_order(xquant.SIDE_BUY, xquant.ORDER_TYPE_LIMIT,
            self.symbol, limit_buy_price, buy_target_amount)
        logging.info('current price: %f;  limit buy price: %f;  order_id: %s ',cur_price, limit_buy_price, order_id)


    def limit_sell(self, target_coin_amount, cur_price):
        if target_coin_amount <= 0:
            return

        logging.info('sell target coin num: %f',target_free_count)
        limit_sell_price = utils.reserve_float(cur_price * 0.9, self.base_amount_digits)
        order_id = self.engine.send_order(xquant.SIDE_SELL, xquant.ORDER_TYPE_LIMIT,
            self.symbol, limit_sell_price, target_coin_amount)
        logging.info('current price: %f;  limit sell price: %f;  order_id: %s',cur_price, limit_sell_price, order_id)


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

		
