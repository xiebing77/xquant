#!/usr/bin/python
from .engine import Engine
from setup import *
from exchange.binanceExchange import BinanceExchange
from exchange.okexExchange import OkexExchange
import common.xquant as xquant
from db.mongodb import MongoDB

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

        self.__db = MongoDB(mongo_user, mongo_pwd, db_name, db_url)


    def get_klines_1day(self, symbol, size):
        return self.__exchange.get_klines_1day(symbol, size)

    def get_balances(self, *coins):
       return self.__exchange.get_balances(*coins)

    def get_position(self, symbol):
        amount = 0
        value = 0
        orders = self.__db.get_orders(strategy_id=self.strategy_id, symbol=symbol)
        for order in orders:
            if order['side'] == xquant.SIDE_BUY:
                amount += order['deal_amount']
                value += order['deal_value']
            elif order['side'] == xquant.SIDE_SELL:
                amount -= order['deal_amount']
                value -= order['deal_value']
            else:
                return
        return amount, value


    def sync_orders(self, symbol):
        orders = self.__db.get_orders(symbol=symbol, status=xquant.ORDER_STATUS_OPEN)
        if len(orders) <= 0:
            return

        df_amount, df_value = self.__exchange.get_deals(symbol)

        for order in orders:
            _id = order['_id']
            order_id = order['orderId']
            deal_amount = df_amount[order_id]
            deal_value = df_value[order_id]

            status = xquant.ORDER_STATUS_OPEN
            if deal_amount > order['deal_amount']:
                continue
            elif deal_amount == order['deal_amount']:
                status = xquant.ORDER_STATUS_CLOSE
            else:
                if self.__exchange.order_status_is_close(order_id):
                    status = xquant.ORDER_STATUS_CLOSE

            self.__db.update_order(id=_id, deal_amount=deal_amount, deal_value=deal_value, status=status)
        return

    def send_order(self, side, type, symbol, price, amount):
        id = self.__db.insert_order(
            strategy_id=self.strategy_id,
            symbol=symbol,
            side=side,
            type=type,
            pirce=price,
            amount=amount,
            status=ORDER_STATUS_WAIT)

        order_id = self.__exchange.send_order(side, type, symbol, price, amount, client_order_id)

        self.__db.update_order(
            id=id,
            order_id=order_id,
            status=xquant.ORDER_STATUS_OPEN)
        return order_id

    def cancle_orders(self, symbol):
        db_orders = self.__db.get_orders(strategy_id=self.strategy_id, symbol=symbol, status=xquant.ORDER_STATUS_OPEN)
        if len(db_orders) <= 0
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
