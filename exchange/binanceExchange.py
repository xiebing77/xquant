#!/usr/bin/python
"""binance适配对接"""
import os
import logging
import pandas as pd
import common.xquant as xq
from .exchange import Exchange
from .binance.client import Client
from .binance.enums import *

api_key = os.environ.get('BINANCE_API_KEY')
secret_key = os.environ.get('BINANCE_SECRET_KEY')


class BinanceExchange(Exchange):
    """BinanceExchange"""
    def __init__(self, debug=False):
        self.__client = Client(api_key, secret_key)

    def __get_coinkey(self, coin):
        """转换binance格式的coin"""
        return coin.upper()

    def __trans_symbol(self, symbol):
        """转换为binance格式的symbol"""
        target_coin, base_coin = xq.get_symbol_coins(symbol)
        return '%s%s' % (self.__get_coinkey(target_coin), self.__get_coinkey(base_coin))

    def __trans_side(self, side):
        """转换为binance格式的side"""
        if side == xq.SIDE_BUY:
            return SIDE_BUY
        elif side == xq.SIDE_SELL:
            return SIDE_SELL
        else:
            return None

    def __trans_type(self, type):
        """转换为binance格式的type"""
        if type == xq.ORDER_TYPE_LIMIT:
            return ORDER_TYPE_LIMIT
        elif type == xq.ORDER_TYPE_MARKET:
            return ORDER_TYPE_MARKET
        else:
            return None

    def __get_klines(self, symbol, interval, size, since):
        """获取k线"""
        exchange_symbol = self.__trans_symbol(symbol)
        if since is None:
            klines = self.__client.get_klines(symbol=exchange_symbol, interval=interval, limit=size)
        else:
            klines = self.__client.get_klines(symbol=exchange_symbol, interval=interval, limit=size, startTime=since)

        df = pd.DataFrame(klines, columns=['open_time', 'open','high','low','close','volume','close_time',
            'quote_asset_volume','number_of_trades','taker_buy_base_asset_volume','taker_buy_quote_asset_volume','ignore'])
        return df

    def get_klines_1day(self, symbol, size=300, since=None):
        """获取日k线"""
        return self.__get_klines(symbol, KLINE_INTERVAL_1DAY, size, since)

    def get_klines_1min(self, symbol, size=300, since=None):
        """获取分钟k线"""
        return self.__get_klines(symbol, KLINE_INTERVAL_1MINUTE, size, since)

    def get_balances(self, *coins):
        """获取余额"""
        coin_balances = []
        account = self.__client.get_account()
        balances = account['balances']
        for coin in coins:
            coinKey = self.__get_coinkey(coin)
            for item in balances:
                if coinKey == item['asset']:
                    balance = xq.create_balance(coin, item['free'], item['locked'])
                    coin_balances.append(balance)
                    break
        if len(coin_balances) <= 0:
            return
        elif len(coin_balances) == 1:
            return coin_balances[0]
        else:
            return tuple(coin_balances)

    def order_status_is_close(self, symbol, order_id):
        """查询委托状态"""
        exchange_symbol = self.__trans_symbol(symbol)
        order = self.__client.get_order(symbol=exchange_symbol, orderId=order_id)
        if order['status'] in [ORDER_STATUS_FILLED, ORDER_STATUS_CANCELED, ORDER_STATUS_REJECTED, ORDER_STATUS_EXPIRED]:
            return True
        return False

    def get_deals(self, symbol, start_time='', end_time='', from_id='', limit=''):
        """获取成交"""
        exchange_symbol = self.__trans_symbol(symbol)
        trades = self.__client.get_my_trades(symbol=exchange_symbol)
        df = pd.DataFrame(trades)
        df[['price','qty']] = df[['price','qty']].apply(pd.to_numeric)
        df['value'] = df['price'] * df['qty']

        df_s = df.groupby('orderId')['qty', 'value'].sum()
        return df_s['qty'], df_s['value']


    def send_order(self, side, type, symbol, price, amount, client_order_id):
        """提交委托"""
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
        """获取挂单"""
        exchange_symbol = self.__trans_symbol(symbol)
        orders = self.__client.get_open_orders(symbol=exchange_symbol)
        return orders

    def cancel_order(self, symbol, order_id):
        """撤单"""
        exchange_symbol = self.__trans_symbol(symbol)
        self.__client.cancel_order(symbol=exchange_symbol, orderId=order_id)


