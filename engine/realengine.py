#!/usr/bin/python
from .engine import Engine
from setup import *
from exchange.binanceExchange import BinanceExchange
from exchange.okexExchange import OkexExchange
import common.xquant as xquant
from db.mongodb import md
import logging

class RealEngine(Engine):
    """docstring for Engine"""
    def __init__(self, exchange, strategy_id):
        self.strategy_id = strategy_id

        if exchange == 'binance':
            self.__exchange = BinanceExchange(debug=True)

        elif exchange == 'okex':
            self.__exchange = OkexExchange(debug=True)

        else:
            print('Wrong exchange name: %s' % exchange)
            exit(1)

        self.__db = md.MongoDB(mongo_user, mongo_pwd, db_name, db_url)


    def get_klines_1day(self, symbol, size):
        return self.__exchange.get_klines_1day(symbol, size)

    def get_balances(self, *coins):
       return self.__exchange.get_balances(*coins)

    def get_position(self, symbol, cur_price):
        self.sync_orders(symbol)

        start_time = None
        position_amount = 0
        buy_value = 0
        sell_value = 0
        orders = self.__db.get_orders(strategy_id=self.strategy_id, symbol=symbol)
        for order in orders:
            if order['side'] == xquant.SIDE_BUY:
                if position_amount == 0:
                    start_time = md.get_datetime_by_id(order['_id'])
                position_amount += order['deal_amount']
                buy_value += order['deal_value']
            elif order['side'] == xquant.SIDE_SELL:
                position_amount -= order['deal_amount']
                sell_value += order['deal_value']
            else:
                logging.error('错误的委托方向')
                return

        profit = 0
        if position_amount == 0:
            profit = sell_value - buy_value
        elif position_amount > 0:
            position_value = cur_price * position_amount
            profit = position_value + sell_value - buy_value
        else:
            logging.error('持仓数量不可能小于0')
            return

        return position_amount, profit, start_time

    def has_open_orders(self, symbol):
        db_orders = self.__db.get_orders(strategy_id=self.strategy_id, symbol=symbol, status=xquant.ORDER_STATUS_OPEN)
        if len(db_orders) > 0:
            return True
        return False

    # 注意：触发是本策略有未完成的委托，但同步是account下所有委托，避免重复查询成交
    def sync_orders(self, symbol):
        if self.has_open_orders(symbol) == False:
            return

        orders = self.__db.get_orders(symbol=symbol, status=xquant.ORDER_STATUS_OPEN)
        if len(orders) <= 0:
            return

        df_amount, df_value = self.__exchange.get_deals(symbol)
        for order in orders:
            logging.debug('order: ', order)
            order_id = order['order_id']
            order_amount = order['amount']

            deal_amount = df_amount[order_id]
            deal_value = df_value[order_id]

            status = xquant.ORDER_STATUS_OPEN
            if deal_amount > order_amount:
                logging.error('最新成交数量大于委托数量')
                continue
            elif deal_amount == order_amount:
                status = xquant.ORDER_STATUS_CLOSE
            else:
                if deal_amount < order['deal_amount']:
                    logging.warning('最新成交数量小于委托里记载的旧成交数量')
                    continue
                elif deal_amount == order['deal_amount']:
                    logging.info('成交数量没有更新')
                else:
                    pass
                if self.__exchange.order_status_is_close(symbol, order_id):
                    status = xquant.ORDER_STATUS_CLOSE
            logging.debug('deal_amount: %s,  deal_value: %s' % (deal_amount, deal_value))
            self.__db.update_order(id=order['_id'], deal_amount=deal_amount, deal_value=deal_value, status=status)
        return

    def send_order(self, side, type, symbol, price, amount):
        id = self.__db.insert_order(
            strategy_id=self.strategy_id,
            symbol=symbol,
            side=side,
            type=type,
            pirce=price,
            amount=amount,
            status=xquant.ORDER_STATUS_WAIT,
            order_id = '',
            cancle_amount = 0,
            deal_amount = 0,
            deal_value = 0)

        order_id = self.__exchange.send_order(side, type, symbol, price, amount, id)

        self.__db.update_order(
            id=id,
            order_id=order_id,
            status=xquant.ORDER_STATUS_OPEN)
        return order_id

    def cancle_orders(self, symbol):
        if self.has_open_orders(symbol) == False:
            return

        orders = self.__exchange.get_open_orders(symbol)
        for order in orders:
            if order['strategy_id'] == self.strategy_id:
                self.__db.update_order(id=order['_id'], status=xquant.ORDER_STATUS_CANCELLING)
                self.__exchange.cancel_order(symbol, order['order_id'])


def test():
    re = RealEngine()
    df = re.get_kline()
    print(df)

if __name__ == "__main__":
    test()
