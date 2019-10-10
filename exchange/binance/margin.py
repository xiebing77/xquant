#!/usr/bin/env python
# coding=utf-8

import hashlib
import hmac
import requests
import six
import time
from .exceptions import BinanceAPIException, BinanceRequestException, BinanceWithdrawException

if six.PY2:
    from urllib import urlencode
elif six.PY3:
    from urllib.parse import urlencode

# https://github.com/binance-exchange/binance-official-api-docs/blob/master/margin-api.md

class Client(object):

    API_URL = 'https://api.binance.com/sapi'
    PUBLIC_API_VERSION = 'v1'

    ORDER_STATUS_NEW = 'NEW'
    ORDER_STATUS_PARTIALLY_FILLED = 'PARTIALLY_FILLED'
    ORDER_STATUS_FILLED = 'FILLED'
    ORDER_STATUS_CANCELED = 'CANCELED'
    ORDER_STATUS_PENDING_CANCEL = 'PENDING_CANCEL'
    ORDER_STATUS_REJECTED = 'REJECTED'
    ORDER_STATUS_EXPIRED = 'EXPIRED'

    KLINE_INTERVAL_1MINUTE = '1m'
    KLINE_INTERVAL_3MINUTE = '3m'
    KLINE_INTERVAL_5MINUTE = '5m'
    KLINE_INTERVAL_15MINUTE = '15m'
    KLINE_INTERVAL_30MINUTE = '30m'
    KLINE_INTERVAL_1HOUR = '1h'
    KLINE_INTERVAL_2HOUR = '2h'
    KLINE_INTERVAL_4HOUR = '4h'
    KLINE_INTERVAL_6HOUR = '6h'
    KLINE_INTERVAL_8HOUR = '8h'
    KLINE_INTERVAL_12HOUR = '12h'
    KLINE_INTERVAL_1DAY = '1d'
    KLINE_INTERVAL_3DAY = '3d'
    KLINE_INTERVAL_1WEEK = '1w'
    KLINE_INTERVAL_1MONTH = '1M'

    SIDE_BUY = 'BUY'
    SIDE_SELL = 'SELL'

    ORDER_TYPE_LIMIT = 'LIMIT'
    ORDER_TYPE_MARKET = 'MARKET'
    ORDER_TYPE_STOP_LOSS = 'STOP_LOSS'
    ORDER_TYPE_STOP_LOSS_LIMIT = 'STOP_LOSS_LIMIT'
    ORDER_TYPE_TAKE_PROFIT = 'TAKE_PROFIT'
    ORDER_TYPE_TAKE_PROFIT_LIMIT = 'TAKE_PROFIT_LIMIT'
    ORDER_TYPE_LIMIT_MAKER = 'LIMIT_MAKER'

    TIME_IN_FORCE_GTC = 'GTC'  # Good till cancelled
    TIME_IN_FORCE_IOC = 'IOC'  # Immediate or cancel
    TIME_IN_FORCE_FOK = 'FOK'  # Fill or kill

    ORDER_RESP_TYPE_ACK = 'ACK'
    ORDER_RESP_TYPE_RESULT = 'RESULT'
    ORDER_RESP_TYPE_FULL = 'FULL'

    def __init__(self, api_key, api_secret):
        """Binance API Client constructor

        :param api_key: Api Key
        :type api_key: str.
        :param api_secret: Api Secret
        :type api_secret: str.

        """

        self.API_KEY = api_key
        self.API_SECRET = api_secret
        self.session = self._init_session()

        # init DNS and SSL cert
        # self.ping()

    def _init_session(self):

        session = requests.session()
        session.headers.update({'Accept': 'application/json',
                                'User-Agent': 'binance/python',
                                'X-MBX-APIKEY': self.API_KEY})
        return session

    def _create_api_uri(self, path, version=PUBLIC_API_VERSION):
        return self.API_URL + '/' + version + '/' + path

    def _create_margin_api_uri(self, path, version=PUBLIC_API_VERSION):
        return self._create_api_uri('margin/' + path, version)

    def _generate_signature(self, data):

        query_string = urlencode(data)
        m = hmac.new(self.API_SECRET.encode('utf-8'),
                     query_string.encode('utf-8'), hashlib.sha256)
        return m.hexdigest()

    def _order_params(self, data):
        """Convert params to list with signature as last element

        :param data:
        :return:

        """
        has_signature = False
        params = []
        for key, value in data.items():
            if key == 'signature':
                has_signature = True
            else:
                params.append((key, value))
        if has_signature:
            params.append(('signature', data['signature']))
        return params

    def _request(self, method, uri, signed, force_params=False, **kwargs):

        data = kwargs.get('data', None)
        if data and isinstance(data, dict):
            kwargs['data'] = data
        if signed:
            # generate signature
            kwargs['data']['timestamp'] = int(time.time() * 1000)
            kwargs['data']['signature'] = self._generate_signature(
                kwargs['data'])

        if data and (method == 'get' or force_params):
            kwargs['params'] = self._order_params(kwargs['data'])
            del(kwargs['data'])

        response = getattr(self.session, method)(uri, **kwargs)
        return self._handle_response(response)

    def _request_api(self, method, path, signed=False, version=PUBLIC_API_VERSION, **kwargs):
        uri = self._create_api_uri(path, version)

        return self._request(method, uri, signed, **kwargs)

    def _handle_response(self, response):
        """Internal helper for handling API responses from the Binance server.
        Raises the appropriate exceptions when necessary; otherwise, returns the
        response.
        """
        if not str(response.status_code).startswith('2'):
            raise BinanceAPIException(response)
        try:
            return response.json()
        except ValueError:
            raise BinanceRequestException(
                'Invalid Response: %s' % response.text)

    def _get(self, path, signed=False, version=PUBLIC_API_VERSION, **kwargs):
        return self._request_api('get', path, signed, version, **kwargs)

    def _post(self, path, signed=False, version=PUBLIC_API_VERSION, **kwargs):
        return self._request_api('post', path, signed, version, **kwargs)

    def _put(self, path, signed=False, version=PUBLIC_API_VERSION, **kwargs):
        return self._request_api('put', path, signed, version, **kwargs)

    def _delete(self, path, signed=False, version=PUBLIC_API_VERSION, **kwargs):
        return self._request_api('delete', path, signed, version, **kwargs)

    # Account Endpoints
    def transfer(self, **params):
        """Execute transfer between spot account and margin account
        """
        return self._post('margin/transfer', True, data=params)

    def loan(self, **params):
        """Apply for a loan
        """
        return self._post('margin/loan', True, data=params)

    def repay(self, **params):
        """Repay loan for margin account.
        """
        return self._post('margin/repay', True, data=params)

    def create_order(self, **params):
        """Send in a new order for margin account
        """
        return self._post('margin/order', True, data=params)

    def order_limit(self, timeInForce=TIME_IN_FORCE_GTC, **params):
        """Send in a new limit order
        """
        params.update({
            'type': self.ORDER_TYPE_LIMIT,
            'timeInForce': timeInForce
        })
        return self.create_order(**params)

    def order_limit_buy(self, timeInForce=TIME_IN_FORCE_GTC, **params):
        """Send in a new limit buy order
        """
        params.update({
            'side': self.SIDE_BUY,
        })
        return self.order_limit(timeInForce=timeInForce, **params)

    def order_limit_sell(self, timeInForce=TIME_IN_FORCE_GTC, **params):
        """Send in a new limit sell order
        """
        params.update({
            'side': self.SIDE_SELL
        })
        return self.order_limit(timeInForce=timeInForce, **params)

    def order_market(self, **params):
        """Send in a new market order
        """
        params.update({
            'type': self.ORDER_TYPE_MARKET
        })
        return self.create_order(**params)

    def order_market_buy(self, **params):
        """Send in a new market buy order
        """
        params.update({
            'side': self.SIDE_BUY
        })
        return self.order_market(**params)

    def order_market_sell(self, **params):
        """Send in a new market sell order
        """
        params.update({
            'side': self.SIDE_SELL
        })
        return self.order_market(**params)

    def cancel_order(self, **params):
        """Cancel an active order for margin account
        """
        return self._delete('margin/order', True, data=params)

    def get_loan(self, **params):
        """Query loan record
        """
        return self._get('margin/loan', True, data=params)

    def get_repay(self, **params):
        """Query repay record
        """
        return self._get('margin/repay', True, data=params)

    def get_account(self, **params):
        """Query margin account detail
        """
        return self._get('margin/account', True, data=params)

    def get_asset(self, **params):
        """Query margin asset
        """
        return self._get('margin/asset', True, data=params)

    def get_pair(self, **params):
        """Query margin pair
        """
        return self._get('margin/pair', True, data=params)

    def get_all_assets(self, **params):
        """Query all margin assets
        """
        return self._get('margin/allAssets', True, data=params)

    def get_all_pairs(self, **params):
        """Query all margin pairs
        """
        return self._get('margin/allPairs', True, data=params)

    def get_price_index(self, **params):
        """Query margin price index
        """
        return self._get('margin/priceIndex', True, data=params)

    def get_transfer_history(self, **params):
        """Query transfer history
        """
        return self._get('margin/transfer', True, data=params)

    def get_interest_history(self, **params):
        """Query interest history
        """
        return self._get('margin/interestHistory', True, data=params)

    def get_force_liquidation_record(self, **params):
        """Query force liquidation record
        """
        return self._get('margin/forceLiquidationRec', True, data=params)

    def get_order(self, **params):
        """Query order
        """
        return self._get('margin/order', True, data=params)

    def get_open_order(self, **params):
        """Query open order
        """
        return self._get('margin/openOrders', True, data=params)

    def get_all_orders(self, **params):
        """Query all orders
        """
        return self._get('margin/allOrders', True, data=params)

    def get_my_trades(self, **params):
        """Query trade list
        """
        return self._get('margin/myTrades', True, data=params)

    def get_max_borrowable(self, **params):
        """Query max borrowable
        """
        return self._get('margin/maxBorrowable', True, data=params)

    def get_max_transferable(self, **params):
        """Query max transferable
        """
        return self._get('margin/maxTransferable', True, data=params)

    def get_loan(self, **params):
        """Query loan record
        """
        return self._get('margin/loan', True, data=params)

    def get_loan(self, **params):
        """Query loan record
        """
        return self._get('margin/loan', True, data=params)

    # User Stream Endpoints
    def stream_get_listen_key(self, **params):
        """Start a new user data stream. The stream will close after 30 minutes unless a keepalive is sent.
        """
        res = self._post('userDataStream', False, data={})
        return res['listenKey']

    def stream_keepalive(self, **params):
        """Keepalive a user data stream to prevent a time out. User data streams will close after 30 minutes. 
        It's recommended to send a ping about every 30 minutes.
        """
        return self._put('userDataStream', False, data=params)

    def stream_close(self, **params):
        """Close out a user data stream.
        """
        return self._delete('userDataStream', False, data=params)
