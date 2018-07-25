#!/usr/bin/python
import os
import common.xquant as xquant
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
        target_coin, base_coin = xquant.get_symbol_coins(symbol)
        return '%s_%s' % (self.__get_coinkey(target_coin), self.__get_coinkey(base_coin))

    def __trans_side(self, side):
        if side == xquant.SIDE_BUY:
            return 'buy'
        elif side == xquant.SIDE_SELL:
            return 'sell'
        else:
            return None

    def __get_klines(self, symbol, interval, size=300, since=''):
        exchange_symbol = __trans_symbol(symbol)

        klines = self.client.get_kline(exchange_symbol, interval, size, since)
        df = pd.DataFrame(klines, columns=['open_time', 'open','high','low','close','volume','close_time'])
        return df

    def get_klines_1day(self, symbol, size, since):
        return self.__get_klines(symbol, '1day', size, since)
        

    def get_balances(self, *coins):
        coin_balances = []
        account = self.client.get_account()
        free = account['free']
        frozen = account['frozen']

        for coin in coins:
            coinKey = self.__get_coinkey(coin)
            balance = self.__create_balance(coin, free[coinKey], frozen[coinKey])
            coin_balances.append(balance)

        return tuple(coin_balances)
 
    def send_order(self, side, type, symbol, price, amount, client_order_id=''):
        exchange_symbol = __trans_symbol(symbol)
        self.debug('send order: pair(%s), side(%s), price(%s), amount(%s)' % (exchange_symbol, side, price, amount))

        okex_side = __trans_side(side)
        if okex_side is None:
            return
      
        if type != xquant.ORDER_TYPE_LIMIT:
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

