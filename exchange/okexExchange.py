#!/usr/bin/python
import os
import common.xquant as xq
from .exchange import Exchange
from .okex.OkcoinSpotAPI import OKCoinSpot

api_key = os.environ.get('OKEX_API_KEY')
secret_key = os.environ.get('OKEX_SECRET_KEY')
rest_url = 'www.okex.com'


class OkexExchange(Exchange):
    """docstring for OkexExchange"""
    def __init__(self, debug=False):
        self.client = OKCoinSpot(rest_url, api_key, secret_key)

    def __get_coinkey(self, coin):
        return coin.lower()

    def __trans_symbol(self, symbol):
        target_coin, base_coin = xq.get_symbol_coins(symbol)
        return '%s_%s' % (self.__get_coinkey(target_coin), self.__get_coinkey(base_coin))

    def __trans_side(self, side):
        if side == xq.SIDE_BUY:
            return 'buy'
        elif side == xq.SIDE_SELL:
            return 'sell'
        else:
            return None

    @staticmethod
    def get_kline_column_names():
        return ['open_time', 'open','high','low','close','volume','close_time']

    def __get_klines(self, symbol, interval, size, since):
        exchange_symbol = __trans_symbol(symbol)
        klines = self.client.get_kline(symbol=exchange_symbol, interval=interval, size=size)
        return klines

    def get_klines_1day(self, symbol, size=300, since=''):
        return self.__get_klines(symbol, '1day', size, since)
        

    def get_balances(self, *coins):
        coin_balances = []
        account = self.client.get_account()
        free = account['free']
        frozen = account['frozen']

        for coin in coins:
            coinKey = self.__get_coinkey(coin)
            balance = xq.create_balance(coin, free[coinKey], frozen[coinKey])
            coin_balances.append(balance)

        if len(coin_balances) <= 0:
            return
        elif len(coin_balances) == 1:
            return coin_balances[0]
        else:
            return tuple(coin_balances)
 
    def send_order(self, side, type, symbol, price, amount, client_order_id=''):
        exchange_symbol = __trans_symbol(symbol)
        self.debug('send order: pair(%s), side(%s), price(%s), amount(%s)' % (exchange_symbol, side, price, amount))

        okex_side = __trans_side(side)
        if okex_side is None:
            return
      
        if type != xq.ORDER_TYPE_LIMIT:
            return

        ret = json.loads(self.client.trade(exchange_symbol, okex_side, price=str(price), amount=str(amount)))
        # self.debug(ret)
        try:
            if ret['result']:
                # self.debug('Return buy order ID: %s' % ret['order_id'])
                return ret['order_id']
            else:
                self.debug('Place order failed')
                return None
        except Exception:
            self.debug('Error result: %s' % ret)
            return None

    def cancel_order(self, symbol, order_id):
        exchange_symbol = self.__trans_symbol(symbol)
        self.client.cancel_order(symbol=exchange_symbol, orderId=order_id)
