#!/usr/bin/python
import os
import common.xquant as xquant
from .exchange import Exchange
from .binance.client import Client
from .binance.enums import *
import pandas as pd
import logging

api_key = os.environ.get('BINANCE_API_KEY')
secret_key = os.environ.get('BINANCE_SECRET_KEY')


class BinanceExchange(Exchange):
    """docstring for BinanceExchange"""
    def __init__(self, debug=False):
        self.__client = Client(api_key, secret_key)

    def __get_coinkey(self, coin):
        return coin.upper()

    def __trans_symbol(self, symbol):
        target_coin, base_coin = xquant.get_symbol_coins(symbol)
        return '%s%s' % (self.__get_coinkey(target_coin), self.__get_coinkey(base_coin))

    def __trans_side(self, side):
        if side == xquant.SIDE_BUY:
            return SIDE_BUY
        elif side == xquant.SIDE_SELL:
            return SIDE_SELL
        else:
            return None

    def __trans_type(self, type):
        if type == xquant.ORDER_TYPE_LIMIT:
            return ORDER_TYPE_LIMIT
        elif type == xquant.ORDER_TYPE_MARKET:
            return ORDER_TYPE_MARKET
        else:
            return None

    def __get_klines(self, symbol, interval, size, since):
        exchange_symbol = self.__trans_symbol(symbol)
        if since is None:
            klines = self.__client.get_klines(symbol=exchange_symbol, interval=interval, limit=size)
        else:
            klines = self.__client.get_klines(symbol=exchange_symbol, interval=interval, limit=size, startTime=since)

        df = pd.DataFrame(klines, columns=['open_time', 'open','high','low','close','volume','close_time',
            'quote_asset_volume','number_of_trades','taker_buy_base_asset_volume','taker_buy_quote_asset_volume','ignore'])
        return df

    def create_symbol(self, base_coin, target_coin):
        return '%s%s' % (self.__get_coinkey(target_coin), self.__get_coinkey(base_coin))

    def get_klines_1day(self, symbol, size=300, since=None):
        return self.__get_klines(symbol, KLINE_INTERVAL_1DAY, size, since)

    def get_klines_1min(self, symbol, size=300, since=None):
        return self.__get_klines(symbol, KLINE_INTERVAL_1MINUTE, size, since)

    def get_balances(self, *coins):
        coin_balances = []
        account = self.__client.get_account()
        balances = account['balances']
        for coin in coins:
            coinKey = self.__get_coinkey(coin)
            for item in balances:
                if coinKey == item['asset']:
                    balance = self.create_balance(coin, item['free'], item['locked'])
                    coin_balances.append(balance)
                    break

        return tuple(coin_balances)

    def order_status_is_close(self, symbol, order_id):
        exchange_symbol = self.__trans_symbol(symbol)
        order = self.__client.get_order(symbol=exchange_symbol, orderId=order_id)
        if order['status'] in [ORDER_STATUS_FILLED, ORDER_STATUS_CANCELED, ORDER_STATUS_REJECTED, ORDER_STATUS_EXPIRED]:
            return True
        return False

    def get_deals(self, symbol, start_time='', end_time='', from_id='', limit=''):
        exchange_symbol = self.__trans_symbol(symbol)
        trades = self.__client.get_my_trades(symbol=exchange_symbol)
        df = pd.DataFrame(trades)
        df[['price','qty']] = df[['price','qty']].apply(pd.to_numeric)
        df['value'] = df['price'] * df['qty']

        df_s = df.groupby('orderId')['qty', 'value'].sum()
        return df_s['qty'], df_s['value']


    def send_order(self, side, type, symbol, price, amount, client_order_id):
        exchange_symbol = self.__trans_symbol(symbol)

        binance_side = self.__trans_side(side)
        if binance_side is None:
            return
        binance_type = self.__trans_type(type)
        if binance_type is None:
            return

        logging.info('send order: pair(%s), side(%s), type(%s), price(%f), amount(%f)' % (exchange_symbol, binance_side, binance_type, price, amount))
        ret = self.__client.create_order(symbol=exchange_symbol, side=binance_side, type=binance_type,
            timeInForce=TIME_IN_FORCE_GTC, price=price, quantity=amount)
        logging.debug(ret)
        try:
            if ret['orderId']:

                #if ret['fills']:

                # self.debug('Return buy order ID: %s' % ret['orderId'])
                return ret['orderId']
            else:
                # self.debug('Place order failed')
                return None
        except Exception:
            # self.debug('Error result: %s' % ret)
            return None

    def get_open_orders(self, symbol):
        exchange_symbol = self.__trans_symbol(symbol)
        orders = self.__client.get_open_orders(symbol=exchange_symbol)
        return orders

    def cancel_orders(self, symbol, order_id):
        exchange_symbol = self.__trans_symbol(symbol)
        self.__client.cancel_order(symbol=exchange_symbol, orderId=order_id)


