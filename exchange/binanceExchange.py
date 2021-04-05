#!/usr/bin/python
"""binance适配对接"""
import os
from datetime import datetime
import common.log as log
import pandas as pd
import common.xquant as xq
import common.kline as kl
import common.bill as bl
from .binance.client import Client
from .binance.enums import *

api_key = os.environ.get('BINANCE_API_KEY')
secret_key = os.environ.get('BINANCE_SECRET_KEY')


class BinanceCommon:
    max_count_of_single_download_kl = 1000

    def _trans_side(self, direction, action):
        """转换为binance格式的side"""
        if action in [bl.OPEN_POSITION, bl.UNLOCK_POSITION]:
            if direction == bl.DIRECTION_LONG:
                return SIDE_BUY
            elif direction == bl.DIRECTION_SHORT:
                return SIDE_SELL
        elif action in [bl.CLOSE_POSITION, bl.LOCK_POSITION]:
            if direction == bl.DIRECTION_LONG:
                return SIDE_SELL
            elif direction == bl.DIRECTION_SHORT:
                return SIDE_BUY
        return None

    def get_time_from_data_ts(self, ts):
        return datetime.fromtimestamp(ts / 1000)

    def get_data_ts_from_time(self, t):
        return int(t.timestamp()) * 1000


class BinanceExchange(BinanceCommon):
    """BinanceExchange"""
    name = 'binance'
    start_time = datetime(2017, 8, 17, 8)
    min_value = 10
    kl_bt_accuracy = kl.KLINE_INTERVAL_1MINUTE

    kline_data_type = kl.KLINE_DATA_TYPE_LIST

    kline_key_open_time  = kl.KLINE_KEY_OPEN_TIME
    kline_key_close_time = kl.KLINE_KEY_CLOSE_TIME
    kline_key_open       = kl.KLINE_KEY_OPEN
    kline_key_close      = kl.KLINE_KEY_CLOSE
    kline_key_high       = kl.KLINE_KEY_HIGH
    kline_key_low        = kl.KLINE_KEY_LOW
    kline_key_volume     = kl.KLINE_KEY_VOLUME

    kline_column_names = [kline_key_open_time, kline_key_open, kline_key_high, kline_key_low,
            kline_key_close, kline_key_volume, kline_key_close_time,
            'quote_asset_volume','number_of_trades','taker_buy_base_asset_volume','taker_buy_quote_asset_volume','ignore']

    kline_idx_open_time   = kl.get_kline_index(kl.KLINE_KEY_OPEN_TIME, kline_column_names)
    kline_idx_close_time  = kl.get_kline_index(kl.KLINE_KEY_CLOSE_TIME, kline_column_names)
    kline_idx_open        = kl.get_kline_index(kl.KLINE_KEY_OPEN, kline_column_names)
    kline_idx_close       = kl.get_kline_index(kl.KLINE_KEY_CLOSE, kline_column_names)
    kline_idx_high        = kl.get_kline_index(kl.KLINE_KEY_HIGH, kline_column_names)
    kline_idx_low         = kl.get_kline_index(kl.KLINE_KEY_LOW, kline_column_names)
    kline_idx_volume      = kl.get_kline_index(kl.KLINE_KEY_VOLUME, kline_column_names)


    def __init__(self, debug=False):
        return

    def connect(self):
        self.__client = Client(api_key, secret_key)

    def __get_coinkey(self, coin):
        """转换binance格式的coin"""
        return coin.upper()

    def __trans_symbol(self, symbol):
        """转换为binance格式的symbol"""
        target_coin, base_coin = xq.get_symbol_coins(symbol)
        return '%s%s' % (self.__get_coinkey(target_coin), self.__get_coinkey(base_coin))

    def __trans_type(self, type):
        """转换为binance格式的type"""
        if type == xq.ORDER_TYPE_LIMIT:
            return ORDER_TYPE_LIMIT
        elif type == xq.ORDER_TYPE_MARKET:
            return ORDER_TYPE_MARKET
        else:
            return None

    def __trans_interval(self, interval):
        if interval == kl.KLINE_INTERVAL_1MINUTE:
            return KLINE_INTERVAL_1MINUTE
        elif interval == kl.KLINE_INTERVAL_3MINUTE:
            return KLINE_INTERVAL_3MINUTE
        elif interval == kl.KLINE_INTERVAL_5MINUTE:
            return KLINE_INTERVAL_5MINUTE
        elif interval == kl.KLINE_INTERVAL_15MINUTE:
            return KLINE_INTERVAL_15MINUTE
        elif interval == kl.KLINE_INTERVAL_30MINUTE:
            return KLINE_INTERVAL_30MINUTE

        elif interval == kl.KLINE_INTERVAL_1HOUR:
            return KLINE_INTERVAL_1HOUR
        elif interval == kl.KLINE_INTERVAL_2HOUR:
            return KLINE_INTERVAL_2HOUR
        elif interval == kl.KLINE_INTERVAL_4HOUR:
            return KLINE_INTERVAL_4HOUR
        elif interval == kl.KLINE_INTERVAL_6HOUR:
            return KLINE_INTERVAL_6HOUR
        elif interval == kl.KLINE_INTERVAL_8HOUR:
            return KLINE_INTERVAL_8HOUR
        elif interval == kl.KLINE_INTERVAL_12HOUR:
            return KLINE_INTERVAL_12HOUR

        elif interval == kl.KLINE_INTERVAL_1DAY:
            return KLINE_INTERVAL_1DAY
        elif interval == kl.KLINE_INTERVAL_3DAY:
            return KLINE_INTERVAL_3DAY

        elif interval == kl.KLINE_INTERVAL_1WEEK:
            return KLINE_INTERVAL_1WEEK

        elif interval == kl.KLINE_INTERVAL_1MONTH:
            return KLINE_INTERVAL_1MONTH

        else:
            return None

    def __get_klines(self, symbol, interval, size, since):
        """获取k线"""
        exchange_symbol = self.__trans_symbol(symbol)
        if since is None:
            klines = self.__client.get_klines(symbol=exchange_symbol, interval=interval, limit=size)
        else:
            klines = self.__client.get_klines(symbol=exchange_symbol, interval=interval, limit=size, startTime=since)

        return klines

    def get_klines(self, symbol, interval, size=300, since=None):
        return self.__get_klines(symbol, self.__trans_interval(interval), size, since)

    def get_klines_1day(self, symbol, size=300, since=None):
        """获取日k线"""
        return self.__get_klines(symbol, KLINE_INTERVAL_1DAY, size, since)

    def get_klines_1min(self, symbol, size=300, since=None):
        """获取分钟k线"""
        return self.__get_klines(symbol, KLINE_INTERVAL_1MINUTE, size, since)

    def get_account(self):
        """获取账户信息"""
        account = self.__client.get_account()
        nb = []
        balances = account['balances']
        for item in balances:
            if float(item['free'])==0 and float(item['locked'])==0:
                continue
            nb.append(item)
        account['balances'] = nb
        return account


    def get_all_balances(self):
        """获取余额"""
        balances = []
        account = self.get_account()
        for item in account['balances']:
            balance = xq.create_balance(item['asset'], item['free'], item['locked'])
            balances.append(balance)
        return balances


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

    def get_trades(self, symbol):
        """获取成交"""
        exchange_symbol = self.__trans_symbol(symbol)
        trades = self.__client.get_my_trades(symbol=exchange_symbol)
        return trades

    def get_deals(self, symbol, start_time='', end_time='', from_id='', limit=''):
        """获取成交"""
        exchange_symbol = self.__trans_symbol(symbol)
        trades = self.__client.get_my_trades(symbol=exchange_symbol)
        df = pd.DataFrame(trades)
        df[['price','qty']] = df[['price','qty']].apply(pd.to_numeric)
        df['value'] = df['price'] * df['qty']

        df_s = df.groupby('orderId')['qty', 'value'].sum()
        return df_s['qty'], df_s['value']

    def send_order(self, direction, action, type, symbol, price, amount, client_order_id=None):
        """提交委托"""
        exchange_symbol = self.__trans_symbol(symbol)

        binance_side = self._trans_side(direction, action)
        if binance_side is None:
            return
        binance_type = self.__trans_type(type)
        if binance_type is None:
            return

        log.info('send order: pair(%s), side(%s), type(%s), price(%f), amount(%f)' % (exchange_symbol, binance_side, binance_type, price, amount))
        ret = self.__client.create_order(symbol=exchange_symbol, side=binance_side, type=binance_type,
            timeInForce=TIME_IN_FORCE_GTC, price=price, quantity=amount)
        log.debug(ret)
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

    def get_open_order_ids(self, symbol):
        """获取挂单id"""
        orders = self.get_open_orders(symbol)
        return [order["orderId"] for order in orders]

    def cancel_order(self, symbol, order_id):
        """撤单"""
        exchange_symbol = self.__trans_symbol(symbol)
        self.__client.cancel_order(symbol=exchange_symbol, orderId=order_id)

    def cancel_orders(self, symbol, order_ids):
        for order_id in order_ids:
            self.cancel_order(symbol, order_id)

    def get_order_book(self, symbol, limit=100):
        """获取挂单列表"""
        exchange_symbol = self.__trans_symbol(symbol)
        books = self.__client.get_order_book(symbol=exchange_symbol, limit=limit)
        return books

