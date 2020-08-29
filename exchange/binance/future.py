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


class Client(object):

    API_URL = 'https://fapi.binance.com/fapi'
    TRANSFER_API_URL = 'https://api.binance.com/sapi'
    PUBLIC_API_VERSION = 'v1'
    PRIVATE_API_VERSION = 'v1'
    TRANSFER_API_VERSION = 'v1'

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
        """Binance API Future constructor

        :param api_key: Api Key
        :type api_key: str.
        :param api_secret: Api Secret
        :type api_secret: str.

        """

        self.API_KEY = api_key
        self.API_SECRET = api_secret
        self.session = self._init_session()

        # init DNS and SSL cert
        self.ping()

    def _init_session(self):

        session = requests.session()
        session.headers.update({'Accept': 'application/json',
                                'User-Agent': 'binance/python',
                                'X-MBX-APIKEY': self.API_KEY})
        return session

    def _create_api_uri(self, path, signed=True, version=PUBLIC_API_VERSION):
        v = self.PRIVATE_API_VERSION if signed else version
        return self.API_URL + '/' + v + '/' + path

    def _create_transfer_api_uri(self, path):
        return self.TRANSFER_API_URL + '/' + self.TRANSFER_API_VERSION + '/' + path

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
        uri = self._create_api_uri(path, signed, version)

        return self._request(method, uri, signed, **kwargs)

    def _request_transfer_api(self, method, path, signed=False, version=TRANSFER_API_VERSION, **kwargs):
        uri = self._create_transfer_api_uri(path)

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

    def _transfer_get(self, path, signed=False, version=TRANSFER_API_VERSION, **kwargs):
        return self._request_transfer_api('get', path, signed, version, **kwargs)

    def _transfer_post(self, path, signed=False, version=TRANSFER_API_VERSION, **kwargs):
        return self._request_transfer_api('post', path, signed, version, **kwargs)

    def _transfer_put(self, path, signed=False, version=TRANSFER_API_VERSION, **kwargs):
        return self._request_transfer_api('put', path, signed, version, **kwargs)

    def _transfer_delete(self, path, signed=False, version=TRANSFER_API_VERSION, **kwargs):
        return self._request_transfer_api('delete', path, signed, version, **kwargs)

    # Exchange Endpoints
    def get_exchange_info(self):
        """Current exchange trading rules and symbol information

        https://binanceapitest.github.io/Binance-Futures-API-doc/market_data/#exchange-information

        :returns: list - List of product dictionaries

        .. code-block:: python

        {
            "exchangeFilters": [],
            "rateLimits": [
                {
                    "interval": "MINUTE",
                    "intervalNum": 1,
                    "limit": 6000,
                    "rateLimitType": "REQUEST_WEIGHT"
                },
                {
                    "interval": "MINUTE",
                    "intervalNum": 1,
                    "limit": 6000,
                    "rateLimitType": "ORDERS"
                }
            ],
            "serverTime": 1565613908500,
            "symbols": [
                {
                    "filters": [
                        {
                            "filterType": "PRICE_FILTER",
                            "maxPrice": "10000000",
                            "minPrice": "0.00000100",
                            "tickSize": "0.00000100"
                        },
                        {
                            "filterType": "LOT_SIZE",
                            "maxQty": "10000000",
                            "minQty": "0.00100000",
                            "stepSize": "0.00100000"
                        },
                        {
                            "filterType": "MARKET_LOT_SIZE",
                            "maxQty": "10000000",
                            "minQty": "0.00100000",
                            "stepSize": "0.00100000"
                        },
                        {
                            "filterType": "MAX_NUM_ORDERS",
                            "limit": 100
                        }
                    ],
                    "maintMarginPercent": "2.5000",
                    "pricePrecision": 2,
                    "quantityPrecision": 3,
                    "requiredMarginPercent": "5.0000",
                    "status": "TRADING",
                    "OrderType": [
                        "LIMIT",
                        "MARKET",
                        "STOP"
                    ],
                    "symbol": "BTCUSDT",
                    "timeInForce": [
                        "GTC",    // Good Till Cancel
                        "IOC",    // Immediate or Cancel
                        "FOK",    // Fill or Kill
                        "GTX"     // Post only or kill
                    ]
                }
            ],
            "timezone": "UTC"
        }
        :raises: BinanceResponseException, BinanceAPIException

        """

        return self._get('exchangeInfo')

    def get_symbol_info(self, symbol):
        """Return information about a symbol

        :param symbol: required e.g BNBBTC
        :type symbol: str

        :returns: Dict if found, None if not

        .. code-block:: python

            {
                "symbol": "ETHBTC",
                "status": "TRADING",
                "baseAsset": "ETH",
                "baseAssetPrecision": 8,
                "quoteAsset": "BTC",
                "quotePrecision": 8,
                "orderTypes": ["LIMIT", "MARKET"],
                "icebergAllowed": false,
                "filters": [
                    {
                        "filterType": "PRICE_FILTER",
                        "minPrice": "0.00000100",
                        "maxPrice": "100000.00000000",
                        "tickSize": "0.00000100"
                    }, {
                        "filterType": "LOT_SIZE",
                        "minQty": "0.00100000",
                        "maxQty": "100000.00000000",
                        "stepSize": "0.00100000"
                    }, {
                        "filterType": "MIN_NOTIONAL",
                        "minNotional": "0.00100000"
                    }
                ]
            }

        :raises: BinanceResponseException, BinanceAPIException

        """

        res = self._get('exchangeInfo')

        for item in res['symbols']:
            if item['symbol'] == symbol.upper():
                return item

        return None

    # General Endpoints

    def ping(self):
        """Test connectivity to the Rest API.

        https://binanceapitest.github.io/Binance-Futures-API-doc/market_data/#test-connectivity
        """
        return self._get('ping')

    def get_server_time(self):
        """Test connectivity to the Rest API and get the current server time.

        https://binanceapitest.github.io/Binance-Futures-API-doc/market_data/#check-server-time
        """
        return self._get('time')

    # Market Data Endpoints

    def get_order_book(self, **params):
        """Get the Order Book for the market

        https://binanceapitest.github.io/Binance-Futures-API-doc/market_data/#order-book

        :param symbol: required
        :type symbol: str
        :param limit:  Default 100; max 1000. Valid limits:[5, 10, 20, 50, 100, 500, 1000]
        :type limit: int

        :returns: API response

        .. code-block:: python

            {
                "lastUpdateId": 1027024,
                "bids": [
                    [
                    "4.00000000",     // PRICE
                    "431.00000000"    // QTY
                    ]
                ],
                "asks": [
                    [
                    "4.00000200",
                    "12.00000000"
                    ]
                ]
            }

        :raises: BinanceResponseException, BinanceAPIException

        """
        return self._get('depth', data=params)

    def get_recent_trades(self, **params):
        """Get recent trades (up to last 500).

        https://binanceapitest.github.io/Binance-Futures-API-doc/market_data/#recent-trades-list

        :param symbol: required
        :type symbol: str
        :param limit:  Default 500; max 1000.
        :type limit: int

        :returns: API response

        .. code-block:: python

            [
                {
                    "id": 28457,
                    "price": "4.00000100",
                    "qty": "12.00000000",
                    "quoteQty": "8000.00",
                    "time": 1499865549590,
                    "isBuyerMaker": true,
                }
            ]

        :raises: BinanceResponseException, BinanceAPIException

        """
        return self._get('trades', data=params)

    def get_historical_trades(self, **params):
        """Get older market historical trades.

        https://binanceapitest.github.io/Binance-Futures-API-doc/market_data/#old-trades-lookup

        :param symbol: required
        :type symbol: str
        :param limit:  Default 500; max 500.
        :type limit: int
        :param fromId:  TradeId to fetch from. Default gets most recent trades.
        :type fromId: str

        :returns: API response

        .. code-block:: python

            [
                {
                    "id": 28457,
                    "price": "4.00000100",
                    "qty": "12.00000000",
                    "quoteQty": "8000.00",
                    "time": 1499865549590,
                    "isBuyerMaker": true,
                }
            ]

        :raises: BinanceResponseException, BinanceAPIException

        """
        return self._get('historicalTrades', data=params)

    def get_aggregate_trades(self, **params):
        """Get compressed, aggregate trades. Trades that fill at the time,
        from the same order, with the same price will have the quantity aggregated.

        https://binanceapitest.github.io/Binance-Futures-API-doc/market_data/#compressedaggregate-trades-list

        :param symbol: required
        :type symbol: str
        :param fromId:  ID to get aggregate trades from INCLUSIVE.
        :type fromId: str
        :param startTime: Timestamp in ms to get aggregate trades from INCLUSIVE.
        :type startTime: int
        :param endTime: Timestamp in ms to get aggregate trades until INCLUSIVE.
        :type endTime: int
        :param limit:  Default 500; max 500.
        :type limit: int

        :returns: API response

        .. code-block:: python

            [
                {
                    "a": 26129,         # Aggregate tradeId
                    "p": "0.01633102",  # Price
                    "q": "4.70443515",  # Quantity
                    "f": 27781,         # First tradeId
                    "l": 27781,         # Last tradeId
                    "T": 1498793709153, # Timestamp
                    "m": true,          # Was the buyer the maker?
                    "M": true           # Was the trade the best price match?
                }
            ]

        :raises: BinanceResponseException, BinanceAPIException

        """
        return self._get('aggTrades', data=params)

    def get_klines(self, **params):
        """Kline/candlestick bars for a symbol. Klines are uniquely identified by their open time.

        https://binanceapitest.github.io/Binance-Futures-API-doc/market_data/#klinecandlestick-data

        :param symbol: required
        :type symbol: str
        :param interval: required
        :type interval: enum
        :param startTime:
        :type startTime: int
        :param endTime:
        :type endTime: int
        :param limit: - Default 500; max 1500.
        :type limit: int

        :returns: API response

        .. code-block:: python

            [
                [
                    1499040000000,      # Open time
                    "0.01634790",       # Open
                    "0.80000000",       # High
                    "0.01575800",       # Low
                    "0.01577100",       # Close
                    "148976.11427815",  # Volume
                    1499644799999,      # Close time
                    "2434.19055334",    # Quote asset volume
                    308,                # Number of trades
                    "1756.87402397",    # Taker buy base asset volume
                    "28.46694368",      # Taker buy quote asset volume
                    "17928899.62484339" # Can be ignored
                ]
            ]

        :raises: BinanceResponseException, BinanceAPIException

        """
        return self._get('klines', data=params)

    def get_mark_price(self, **params):
        """mark price and funding rate.

        https://binanceapitest.github.io/Binance-Futures-API-doc/market_data/#mark-price

        :param symbol: required
        :type symbol: str

        :returns: API response

        .. code-block:: python

            {
                "symbol": "BTCUSDT",
                "markPrice": "11012.80409769",
                "lastFundingRate": "-0.03750000",
                "nextFundingTime": 1562569200000,
                "time": 1562566020000
            }

        :raises: BinanceResponseException, BinanceAPIException

        """
        return self._get('premiumIndex', data=params)

    def get_ticker(self, **params):
        """24 hour price change statistics.

        https://binanceapitest.github.io/Binance-Futures-API-doc/market_data/#24hr-ticker-price-change-statistics

        :param symbol:
        :type symbol: str

        :returns: API response

        .. code-block:: python

            {
                "priceChange": "-94.99999800",
                "priceChangePercent": "-95.960",
                "weightedAvgPrice": "0.29628482",
                "prevClosePrice": "0.10002000",
                "lastPrice": "4.00000200",
                "bidPrice": "4.00000000",
                "askPrice": "4.00000200",
                "openPrice": "99.00000000",
                "highPrice": "100.00000000",
                "lowPrice": "0.10000000",
                "volume": "8913.30000000",
                "openTime": 1499783499040,
                "closeTime": 1499869899040,
                "fristId": 28385,   # First tradeId
                "lastId": 28460,    # Last tradeId
                "count": 76         # Trade count
            }

        OR

        .. code-block:: python

            [
                {
                    "priceChange": "-94.99999800",
                    "priceChangePercent": "-95.960",
                    "weightedAvgPrice": "0.29628482",
                    "prevClosePrice": "0.10002000",
                    "lastPrice": "4.00000200",
                    "bidPrice": "4.00000000",
                    "askPrice": "4.00000200",
                    "openPrice": "99.00000000",
                    "highPrice": "100.00000000",
                    "lowPrice": "0.10000000",
                    "volume": "8913.30000000",
                    "openTime": 1499783499040,
                    "closeTime": 1499869899040,
                    "fristId": 28385,   # First tradeId
                    "lastId": 28460,    # Last tradeId
                    "count": 76         # Trade count
                }
            ]

        :raises: BinanceResponseException, BinanceAPIException

        """
        return self._get('ticker/24hr', data=params)

    def get_symbol_ticker(self, **params):
        """Latest price for a symbol or symbols.

        https://binanceapitest.github.io/Binance-Futures-API-doc/market_data/#symbol-price-ticker

        :param symbol: required
        :type symbol: str

        :returns: API response

        .. code-block:: python

            {
                "symbol": "BTCUSDT",
                "price": "6000.01"
            }

        :raises: BinanceResponseException, BinanceAPIException

        """
        return self._get('ticker/price', data=params)

    def get_orderbook_ticker(self, **params):
        """Best price/qty on the order book for a symbol or symbols.

        https://binanceapitest.github.io/Binance-Futures-API-doc/market_data/#symbol-order-book-ticker

        :param symbol: required
        :type symbol: str

        :returns: API response

        .. code-block:: python

            {
                "symbol": "BTCUSDT",
                "bidPrice": "4.00000000",
                "bidQty": "431.00000000",
                "askPrice": "4.00000200",
                "askQty": "9.00000000"
            }

        :raises: BinanceResponseException, BinanceAPIException

        """
        return self._get('ticker/bookTicker', data=params)

    # Account Endpoints

    def transfer(self, **params):
        """Execute transfer between spot account and future account

        https://binanceapitest.github.io/Binance-Futures-API-doc/trade_and_account/#new-future-account-transfer
        :param asset: required
        :type asset: str
        :param amount: required
        :type amount: decimal
        :param type: required
        :type type: int
        :param recvWindow: 
        :type recvWindow: long

        :returns: API response

        .. code-block:: python

            {
                "tranId": 100000001    //transaction id
            }

        :raises: BinanceResponseException, BinanceAPIException, BinanceOrderException, BinanceOrderMinAmountException, BinanceOrderMinPriceException, BinanceOrderMinTotalException, BinanceOrderUnknownSymbolException, BinanceOrderInactiveSymbolException

        """
        return self._transfer_post('futures/transfer', True, data=params)

    def get_transfer_history(self, **params):
        """Get future account transaction history list

        https://binanceapitest.github.io/Binance-Futures-API-doc/trade_and_account/#get-future-account-trans-history-list        :param asset: required
        :type asset: str
        :param startTime: required
        :type startTime: long
        :param endTime: 
        :type endTime: long
        :param current: Currently querying page. Start from 1. Default:1
        :type current: long
        :param size: Default:10 Max:100
        :type size: long
        :param recvWindow: 
        :type recvWindow: long

        :returns: API response

        .. code-block:: python

            {
                "rows": [
                    {
                    "asset": "USDT",
                    "tranId": 100000001
                    "amount": "40.84624400",
                    "type": "1"
                    "timestamp": 1555056425000,
                    "status": "CONFIRMED".          //one of PENDING (pending to execution), CONFIRMED (successfully transfered), FAILED (execution failed, nothing happened to your account);
                    }
                ],
                "total": 1
            }
        :raises: BinanceResponseException, BinanceAPIException, BinanceOrderException, BinanceOrderMinAmountException, BinanceOrderMinPriceException, BinanceOrderMinTotalException, BinanceOrderUnknownSymbolException, BinanceOrderInactiveSymbolException

        """
        return self._transfer_get('futures/transfer', True, data=params)

    def create_order(self, **params):
        """Send in a new order

        https://binanceapitest.github.io/Binance-Futures-API-doc/trade_and_account/#new-order-trade

        Any order with an icebergQty MUST have timeInForce set to GTC.

        :param symbol: required
        :type symbol: str
        :param side: required
        :type side: enum
        :param type: required
        :type type: enum
        :param timeInForce: required if limit order
        :type timeInForce: enum
        :param quantity: required
        :type quantity: decimal
        :param price: required
        :type price: decimal
        :param newClientOrderId: A unique id for the order. Automatically generated if not sent.
        :type newClientOrderId: str
        :param stopPrice: Used with STOP orders.
        :type stopPrice: decimal
        :param recvWindow: 
        :type recvWindow: long

        :returns: API response

        Response ACK:

        .. code-block:: python

            {
                "symbol":"LTCBTC",
                "orderId": 1,
                "clientOrderId": "myOrder1" # Will be newClientOrderId
                "transactTime": 1499827319559
            }

        :raises: BinanceResponseException, BinanceAPIException, BinanceOrderException, BinanceOrderMinAmountException, BinanceOrderMinPriceException, BinanceOrderMinTotalException, BinanceOrderUnknownSymbolException, BinanceOrderInactiveSymbolException

        """
        return self._post('order', True, data=params)

    def order_limit(self, timeInForce=TIME_IN_FORCE_GTC, **params):
        """Send in a new limit order

        Any order with an icebergQty MUST have timeInForce set to GTC.

        :param symbol: required
        :type symbol: str
        :param side: required
        :type side: enum
        :param quantity: required
        :type quantity: decimal
        :param price: required
        :type price: decimal
        :param timeInForce: default Good till cancelled
        :type timeInForce: enum
        :param newClientOrderId: A unique id for the order. Automatically generated if not sent.
        :type newClientOrderId: str
        :param stopPrice: Used with STOP orders.
        :type stopPrice: decimal
        :param recvWindow: 
        :type recvWindow: long

        :returns: API response

        See order endpoint for full response options

        :raises: BinanceResponseException, BinanceAPIException, BinanceOrderException, BinanceOrderMinAmountException, BinanceOrderMinPriceException, BinanceOrderMinTotalException, BinanceOrderUnknownSymbolException, BinanceOrderInactiveSymbolException

        """
        params.update({
            'type': self.ORDER_TYPE_LIMIT,
            'timeInForce': timeInForce
        })
        return self.create_order(**params)

    def order_limit_buy(self, timeInForce=TIME_IN_FORCE_GTC, **params):
        """Send in a new limit buy order

        Any order with an icebergQty MUST have timeInForce set to GTC.

        :param symbol: required
        :type symbol: str
        :param quantity: required
        :type quantity: decimal
        :param price: required
        :type price: decimal
        :param timeInForce: default Good till cancelled
        :type timeInForce: enum
        :param newClientOrderId: A unique id for the order. Automatically generated if not sent.
        :type newClientOrderId: str
        :param stopPrice: Used with stop orders
        :type stopPrice: decimal
        :param icebergQty: Used with iceberg orders
        :type icebergQty: decimal
        :param newOrderRespType: Set the response JSON. ACK, RESULT, or FULL; default: RESULT.
        :type newOrderRespType: enum

        :returns: API response

        See order endpoint for full response options

        :raises: BinanceResponseException, BinanceAPIException, BinanceOrderException, BinanceOrderMinAmountException, BinanceOrderMinPriceException, BinanceOrderMinTotalException, BinanceOrderUnknownSymbolException, BinanceOrderInactiveSymbolException

        """
        params.update({
            'side': self.SIDE_BUY,
        })
        return self.order_limit(timeInForce=timeInForce, **params)

    def order_limit_sell(self, timeInForce=TIME_IN_FORCE_GTC, **params):
        """Send in a new limit sell order

        :param symbol: required
        :type symbol: str
        :param quantity: required
        :type quantity: decimal
        :param price: required
        :type price: decimal
        :param timeInForce: default Good till cancelled
        :type timeInForce: enum
        :param newClientOrderId: A unique id for the order. Automatically generated if not sent.
        :type newClientOrderId: str
        :param stopPrice: Used with stop orders
        :type stopPrice: decimal
        :param icebergQty: Used with iceberg orders
        :type icebergQty: decimal

        :returns: API response

        See order endpoint for full response options

        :raises: BinanceResponseException, BinanceAPIException, BinanceOrderException, BinanceOrderMinAmountException, BinanceOrderMinPriceException, BinanceOrderMinTotalException, BinanceOrderUnknownSymbolException, BinanceOrderInactiveSymbolException

        """
        params.update({
            'side': self.SIDE_SELL
        })
        return self.order_limit(timeInForce=timeInForce, **params)

    def order_market(self, **params):
        """Send in a new market order

        :param symbol: required
        :type symbol: str
        :param side: required
        :type side: enum
        :param quantity: required
        :type quantity: decimal
        :param newClientOrderId: A unique id for the order. Automatically generated if not sent.
        :type newClientOrderId: str
        :param newOrderRespType: Set the response JSON. ACK, RESULT, or FULL; default: RESULT.
        :type newOrderRespType: enum

        :returns: API response

        See order endpoint for full response options

        :raises: BinanceResponseException, BinanceAPIException, BinanceOrderException, BinanceOrderMinAmountException, BinanceOrderMinPriceException, BinanceOrderMinTotalException, BinanceOrderUnknownSymbolException, BinanceOrderInactiveSymbolException

        """
        params.update({
            'type': self.ORDER_TYPE_MARKET
        })
        return self.create_order(**params)

    def order_market_buy(self, **params):
        """Send in a new market buy order

        :param symbol: required
        :type symbol: str
        :param quantity: required
        :type quantity: decimal
        :param newClientOrderId: A unique id for the order. Automatically generated if not sent.
        :type newClientOrderId: str
        :param newOrderRespType: Set the response JSON. ACK, RESULT, or FULL; default: RESULT.
        :type newOrderRespType: enum

        :returns: API response

        See order endpoint for full response options

        :raises: BinanceResponseException, BinanceAPIException, BinanceOrderException, BinanceOrderMinAmountException, BinanceOrderMinPriceException, BinanceOrderMinTotalException, BinanceOrderUnknownSymbolException, BinanceOrderInactiveSymbolException

        """
        params.update({
            'side': self.SIDE_BUY
        })
        return self.order_market(**params)

    def order_market_sell(self, **params):
        """Send in a new market sell order

        :param symbol: required
        :type symbol: str
        :param quantity: required
        :type quantity: decimal
        :param newClientOrderId: A unique id for the order. Automatically generated if not sent.
        :type newClientOrderId: str
        :param newOrderRespType: Set the response JSON. ACK, RESULT, or FULL; default: RESULT.
        :type newOrderRespType: enum

        :returns: API response

        See order endpoint for full response options

        :raises: BinanceResponseException, BinanceAPIException, BinanceOrderException, BinanceOrderMinAmountException, BinanceOrderMinPriceException, BinanceOrderMinTotalException, BinanceOrderUnknownSymbolException, BinanceOrderInactiveSymbolException

        """
        params.update({
            'side': self.SIDE_SELL
        })
        return self.order_market(**params)

    def create_test_order(self, **params):
        """Test new order creation and signature/recvWindow long. Creates and validates a new order but does not send it into the matching engine.

        :param symbol: required
        :type symbol: str
        :param side: required
        :type side: enum
        :param type: required
        :type type: enum
        :param timeInForce: required if limit order
        :type timeInForce: enum
        :param quantity: required
        :type quantity: decimal
        :param price: required
        :type price: decimal
        :param newClientOrderId: A unique id for the order. Automatically generated if not sent.
        :type newClientOrderId: str
        :param icebergQty: Used with iceberg orders
        :type icebergQty: decimal
        :param newOrderRespType: Set the response JSON. ACK, RESULT, or FULL; default: RESULT.
        :type newOrderRespType: enum
        :param recvWindow: The number of milliseconds the request is valid for
        :type recvWindow: int

        :returns: API response

        .. code-block:: python

            {}

        :raises: BinanceResponseException, BinanceAPIException, BinanceOrderException, BinanceOrderMinAmountException, BinanceOrderMinPriceException, BinanceOrderMinTotalException, BinanceOrderUnknownSymbolException, BinanceOrderInactiveSymbolException


        """
        return self._post('order/test', True, data=params)

    def get_order(self, **params):
        """Check an order's status. Either orderId or origClientOrderId must be sent.
        Either orderId or origClientOrderId must be sent.

        https://binanceapitest.github.io/Binance-Futures-API-doc/trade_and_account/#query-order-user_data

        :param symbol: required
        :type symbol: str
        :param orderId: The unique order id
        :type orderId: int
        :param origClientOrderId: optional
        :type origClientOrderId: str
        :param recvWindow: the number of milliseconds the request is valid for
        :type recvWindow: int

        :returns: API response

        .. code-block:: python

            {
                "symbol": "BTCUSDT",
                "orderId": 1,
                "clientOrderId": "myOrder1",
                "price": "0.1",
                "origQty": "1.0",
                "executedQty": "0.0",
                "cumQuote": "0.0",
                "status": "NEW",
                "timeInForce": "GTC",
                "type": "LIMIT",
                "side": "BUY",
                "stopPrice": "0.0",
                "time": 1499827319559,
                "updateTime": 1499827319559
            }
        :raises: BinanceResponseException, BinanceAPIException

        """
        return self._get('order', True, data=params)

    def cancel_order(self, **params):
        """Cancel an active order. Either orderId or origClientOrderId must be sent.

        https://binanceapitest.github.io/Binance-Futures-API-doc/trade_and_account/#cancel-order-trade

        :param symbol: required
        :type symbol: str
        :param orderId: The unique order id
        :type orderId: int
        :param origClientOrderId: optional
        :type origClientOrderId: str
        :param newClientOrderId: Used to uniquely identify this cancel. Automatically generated by default.
        :type newClientOrderId: str
        :param recvWindow: the number of milliseconds the request is valid for
        :type recvWindow: int

        :returns: API response

        .. code-block:: python

            {
                "symbol": "BTCUSDT",
                "orderId": 28,
                "origClientOrderId": "myOrder1",
                "clientOrderId": "cancelMyOrder1",
                "transactTime": 1507725176595,
                "price": "1.00000000",
                "origQty": "10.00000000",
                "executedQty": "8.00000000",
                "cumQuote": "8.00000000",
                "status": "CANCELED",
                "timeInForce": "GTC",
                "type": "LIMIT",
                "side": "SELL"
            }
        :raises: BinanceResponseException, BinanceAPIException

        """
        return self._delete('order', True, data=params)

    def get_open_orders(self, **params):
        """Get all open orders on a symbol.

        https://binanceapitest.github.io/Binance-Futures-API-doc/trade_and_account/#current-open-orders-user_data

        :param symbol: required
        :type symbol: str
        :param recvWindow: the number of milliseconds the request is valid for
        :type recvWindow: int

        :returns: API response

        .. code-block:: python

            [
                {
                    "symbol": "BTCUSDT",
                    "orderId": 1,
                    "clientOrderId": "myOrder1",
                    "price": "0.1",
                    "origQty": "1.0",
                    "executedQty": "1.0",
                    "cumQuote": "10.0",
                    "status": "NEW",
                    "timeInForce": "GTC",
                    "type": "LIMIT",
                    "side": "BUY",
                    "stopPrice": "0.0",
                    "updateTime": 1499827319559
                }
            ]

        :raises: BinanceResponseException, BinanceAPIException

        """
        return self._get('openOrders', True, data=params)

    def get_all_orders(self, **params):
        """Get all account orders; active, canceled, or filled. 
        If orderId is set, it will get orders >= that orderId. Otherwise most recent orders are returned.

        https://binanceapitest.github.io/Binance-Futures-API-doc/trade_and_account/#all-orders-user_data

        :param symbol: required
        :type symbol: str
        :param orderId: The unique order id
        :type orderId: int
        :param startTime: 
        :type startTime: long
        :param endTime: 
        :type endTime: long
        :param limit: Default 500; max 500.
        :type limit: int
        :param recvWindow: the number of milliseconds the request is valid for
        :type recvWindow: int

        :returns: API response

        .. code-block:: python
            [
                {
                    "symbol": "BTCUSDT",
                    "orderId": 1,
                    "clientOrderId": "myOrder1",
                    "price": "0.1",
                    "origQty": "1.0",
                    "executedQty": "1.0",
                    "cumQuote": "10.0",
                    "status": "NEW",
                    "timeInForce": "GTC",
                    "type": "LIMIT",
                    "side": "BUY",
                    "stopPrice": "0.0",
                    "updateTime": 1499827319559
                }
            ]
        :raises: BinanceResponseException, BinanceAPIException

        """
        return self._get('allOrders', True, data=params)

    # User Stream Endpoints
    def get_balance(self, **params):
        """Get future account balance.

        https://binanceapitest.github.io/Binance-Futures-API-doc/trade_and_account/#future-account-balance-user_data
        
        :param recvWindow: the number of milliseconds the request is valid for
        :type recvWindow: int

        :returns: API response

        .. code-block:: python
        {
            "accountId": 26
            "asset": "USDT"
            "balance": "122607.35137903"
            "withdrawAvailable": "102333.54137903"
        }
        :raises: BinanceResponseException, BinanceAPIException

        """
        return self._get('balance', True, data=params)

    def get_account(self, **params):
        """Get current account information.

        https://binanceapitest.github.io/Binance-Futures-API-doc/trade_and_account/#account-information-user_data

        :param recvWindow: the number of milliseconds the request is valid for
        :type recvWindow: int

        :returns: API response

        .. code-block:: python
        {
            "assets": [
                {
                    "asset": "USDT",
                    "initialMargin": "9.00000000",
                    "maintMargin": "0.00000000",
                    "marginBalance": "22.12659734",
                    "maxWithdrawAmount": "13.12659734",
                    "openOrderInitialMargin": "9.00000000",
                    "positionInitialMargin": "0.00000000",
                    "unrealizedProfit": "0.00000000",
                    "walletBalance": "22.12659734"
                }
            ],
            "canDeposit": True,
            "canTrade": True,
            "canWithdraw": True,
            "feeTier": 0,
            "maxWithdrawAmount": "13.12659734",
            "totalInitialMargin": "9.00000000",
            "totalMaintMargin": "0.00000000",
            "totalMarginBalance": "22.12659734",
            "totalOpenOrderInitialMargin": u"9.00000000",
            "totalPositionInitialMargin": u"0.00000000",
            "totalUnrealizedProfit": u"0.00000000",
            "totalWalletBalance": u"22.12659734",
            "updateTime": 0

        }
        :raises: BinanceResponseException, BinanceAPIException

        """
        return self._get('account', True, data=params)

    def get_position_risk(self, **params):
        """Get position information.

        https://binanceapitest.github.io/Binance-Futures-API-doc/trade_and_account/#position-information-user_data

        :param recvWindow: the number of milliseconds the request is valid for
        :type recvWindow: int

        :returns: API response

        .. code-block:: python
        [
            {
                "entryPrice": "9975.12000",
                "liquidationPrice": "7963.54",
                "markPrice": "9973.50770517",
                "positionAmt": "0.010",
                "symbol": "BTCUSDT",
                "unRealizedProfit": "-0.01612295"
            }
        ]
        :raises: BinanceResponseException, BinanceAPIException

        """
        return self._get('positionRisk', True, data=params)

    def get_my_trades(self, **params):
        """Get trades for a specific account and symbol.

        https://binanceapitest.github.io/Binance-Futures-API-doc/trade_and_account/#account-trade-list-user_data

        :param symbol: required
        :type symbol: str
        :param startTime: 
        :type startTime: long
        :param endTime: 
        :type endTime: long
        :param fromId: TradeId to fetch from. Default gets most recent trades.
        :type fromId: int
        :param limit: Default 500; max 500.
        :type limit: int
        :param recvWindow: the number of milliseconds the request is valid for
        :type recvWindow: int

        :returns: API response

        .. code-block:: python
        [
            {
                "accountId": 20,
                "buyer": False,
                "commission": "-0.07819010",
                "commissionAsset": "USDT",
                "counterPartyId": 653,
                "id": 698759,
                "maker": False,
                "orderId": 25851813,
                "price": "7819.01",
                "qty": "0.002",
                "quoteQty": "0.01563",
                "realizedPnl": "-0.91539999",
                "side": "SELL",
                "symbol": "BTCUSDT",
                "time": 1569514978020
            }
        ]
        :raises: BinanceResponseException, BinanceAPIException

        """
        return self._get('userTrades', True, data=params)

    # User Stream Endpoints

    def stream_get_listen_key(self, **params):
        """Start a new user data stream. The stream will close after 30 minutes unless a keepalive is sent.

        https://binanceapitest.github.io/Binance-Futures-API-doc/userdatastream/#user-data-stream-endpoints
        
        :param recvWindow: the number of milliseconds the request is valid for
        :type recvWindow: int

        :returns: API response

        .. code-block:: python

            {
                "listenKey": "pqia91ma19a5s61cv6a81va65sdf19v8a65a1a5s61cv6a81va65sdf19v8a65a1"
            }

        :raises: BinanceResponseException, BinanceAPIException

        """
        return self._post('listenKey', True, data=params)

    def stream_keepalive(self, **params):
        """Keepalive a user data stream to prevent a time out. User data streams will close after 30 minutes. 
        It's recommended to send a ping about every 30 minutes.

        https://binanceapitest.github.io/Binance-Futures-API-doc/userdatastream/#user-data-stream-endpoints

        :param recvWindow: the number of milliseconds the request is valid for
        :type recvWindow: int

        :returns: API response

        .. code-block:: python

            {}

        :raises: BinanceResponseException, BinanceAPIException

        """
        return self._put('listenKey', True, data=params)

    def stream_close(self, **params):
        """Close out a user data stream.

        https://binanceapitest.github.io/Binance-Futures-API-doc/userdatastream/#user-data-stream-endpoints

        :param recvWindow: the number of milliseconds the request is valid for
        :type recvWindow: int

        :returns: API response

        .. code-block:: python

            {}

        :raises: BinanceResponseException, BinanceAPIException

        """
        return self._delete('listenKey', True, data=params)
