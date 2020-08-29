#!/usr/bin/python3
import os
from exchange.binance.future import Client
from exchange.binance.enums import *

api_key = os.environ.get('BINANCE_API_KEY')
secret_key = os.environ.get('BINANCE_SECRET_KEY')

if __name__ == "__main__":
    client = Client(api_key, secret_key)
    # ret = client.get_symbol_info(symbol='BTCUSDT')
    # ret = client.get_order_book(symbol='BTCUSDT', limit=10)
    # ret = client.get_recent_trades(symbol='BTCUSDT', limit=10)
    # ret = client.get_historical_trades(symbol='BTCUSDT', limit=10)
    # ret = client.get_klines(symbol='BTCUSDT', interval=KLINE_INTERVAL_1DAY ,limit=10)
    # ret = client.get_mark_price(symbol='BTCUSDT')
    # ret = client.get_ticker(symbol='BTCUSDT')
    # ret = client.get_symbol_ticker(symbol='BTCUSDT')
    # ret = client.get_orderbook_ticker(symbol='BTCUSDT')
    # ret = client.transfer(asset='USDT', amount='20', type=1)
    # ret = client.transfer(asset='USDT', amount='10', type=2)
    # ret = client.get_transfer_history(asset='USDT', startTime=1598696422)
    # ret = client.order_limit_buy(symbol='ETHUSDT', quantity=0.1, price=380)
    # ret = client.order_limit_sell(symbol='ETHUSDT', quantity=0.1, price=450)
    # ret = client.get_order(symbol='ETHUSDT', orderId='2891778466')
    ret = client.cancel_order(symbol='ETHUSDT', orderId='2891900482')
    # ret = client.get_open_orders()
    # ret = client.get_all_orders(symbol='ETHUSDT')
    # ret = client.get_balance()
    # ret = client.get_account()
    # ret = client.get_position_risk()
    # ret = client.get_my_trades(symbol='ETHUSDT')
    # ret = client.stream_get_listen_key()
    # ret = client.stream_keepalive(listenKey='xkSWWmFJRj0yl1uCdZhfdulBPlRqeCbc5KKmfUJix8aPhy8MCnVOjbwIhJoydxbb')
    # ret = client.stream_close(listenKey='xkSWWmFJRj0yl1uCdZhfdulBPlRqeCbc5KKmfUJix8aPhy8MCnVOjbwIhJoydxbb')
    
    print(ret)
